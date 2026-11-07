"""通用循环截图服务（原神 / 崩铁 / 鸣潮 所有功能共用）。

设计目标
--------
1. **全局只有一个后台线程在循环截图**。原实现在 ``func.check.check``、
   ``games.starRail.action.bt_func.check``、``shou_pic.check`` 里各自起了
   一个截图线程，而且每轮还会重复调用两次 ``get_pic``（单次 PrintWindow
   开销约 10~30ms），三个游戏同时跑时 CPU 浪费严重。
2. **所有功能共享同一份最新画面**。任何模块调用 ``get_pic(title)`` 或
   读取 ``check.processed_screen`` 拿到的都是同一帧。
3. **对调用方透明**。``func.get_pic.get_pic(window_title)`` 签名不变，
   服务未启动时自动回退为单次实时截图，老代码无需改动。

自愈层次（从轻到重）
--------------------
1. 单帧：``PW_RENDERFULLCONTENT`` 失败 -> 降级 ``PW_CLIENTONLY`` -> 还不行就抓
   屏幕（只在确认「整个屏幕都是本窗口」时才回退，见 BITBLT_FALLBACK）。
2. 窗口：被最小化就主动还原；全屏游戏被切到后台且用户空闲时抢回前台
   （见 RECOVER_INTERVAL / RECOVER_MAX_INTERVAL）。
3. 线程：连续失败 ``HARD_RESTART_AFTER_FAILURES``（10 次 ≈ 10 秒）次，或者超过
   ``LOOP_HANG_TIMEOUT`` 没有心跳（说明卡死在 PrintWindow/GetDC 这类系统调用
   里，Python 侧打不断）-> 看门狗**杀掉旧线程、重新拉起新线程**（restart_capture），
   日志会打印「已杀掉截图线程（第 N 次），正在重新拉起：原因」。
4. 进程：线程换了几次还是一帧都抓不到（``CAPTURE_DEAD_SECONDS``）-> 任务子进程
   里的看护上报 ``capture_dead``，界面默认**只报警**（不擅自杀任务进程、不抢
   焦点）；需要时可以把 ``main_window.AUTO_RESTART_ON_CAPTURE_DEAD`` 打开，由
   ``TaskRunner.restart()`` 收掉整棵进程树、按原参数重新拉起。

线程安全
--------
循环线程每轮都会创建一个**全新的 ndarray** 再赋值给 ``_frame``，从不原地
修改已经发布出去的帧；而 ``_frame = frame`` 在 CPython 下是原子引用赋值。
因此 :meth:`ScreenshotService.latest` 可以零拷贝返回引用——调用方持有的
旧帧永远是完整的一帧，不会读到半新半旧的撕裂画面。

典型用法
--------
    from func import screenshot

    screenshot.start_capture('原神')       # 启动（进程内单例）
    frame = screenshot.latest('原神')       # 取最新一帧，可能为 None
    screenshot.is_stale()                   # 画面是否已陈旧（截图连续失败）
    screenshot.restart_capture()            # 彻底重启截图线程（放弃卡死的旧线程）
    screenshot.stop_capture()               # 停止

    # 兼容老写法（会自动走共享缓存）
    from func.get_pic import get_pic
    frame = get_pic('原神')
"""

import ctypes
import threading
import time

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32process
import win32ui
from ctypes import windll

from func.common import get_hwnd, log, setting

# 循环截图默认间隔（秒）。原实现靠 get_pic 自身耗时来节流，这里显式给出。
DEFAULT_INTERVAL = 0.01

# 连续失败多少帧之后，认为当前画面已经「陈旧」：调用方（check 类）不应该
# 再拿它做判断，否则会按过期界面乱点（表现就是「功能失效、乱点」）。
STALE_AFTER_FAILURES = 3

# 截图失败日志的最小间隔（秒）。PrintWindow 一旦开始失败就是每帧都失败，
# 20~100Hz 地 log 会把终端 / IDE 刷爆（也是用户看到的「持续报错」），所以限频。
FAIL_LOG_INTERVAL = 5.0

# 截图连续失败时的重试间隔（秒）。一直失败通常是窗口被最小化 / 被完全遮挡，
# 或者游戏正在加载、一时没有响应；这时候继续按 DEFAULT_INTERVAL 高频重试
# 只会把窗口的消息队列刷爆（越刷越卡），所以失败期间降频，恢复后自动还原。
FAIL_RETRY_INTERVAL = 1.0

# 失败时「重新按标题找窗口」的最小间隔（秒）。原来每失败一次就枚举一遍所有
# 窗口（还带跨进程的标题读取），失败期间 20~100Hz 地做这件事纯属浪费；而且
# 万一枚举过程中被别的窗口卡住，截图线程就整个钉死了，所以限频。
RESOLVE_INTERVAL = 3.0

# 窗口被最小化 / 被别的窗口压住时，最多每 RECOVER_INTERVAL 秒尝试一次自愈；
# 连续失败会指数退避，最长退到 RECOVER_MAX_INTERVAL 秒（避免一直抢前台）。
RECOVER_INTERVAL = 15.0
RECOVER_MAX_INTERVAL = 300.0

# ---------------------------------------------------------------------------
# 「彻底重启截图线程」的阈值（用户看到的「彻底杀掉截图重新拉起」）
# ---------------------------------------------------------------------------
# 连续失败多少次之后，认为截图线程**已经救不回来**了，换一个新线程重来。
# 失败期间的重试间隔是 FAIL_RETRY_INTERVAL（1s），所以 10 次大约等于「10 秒
# 一帧都没抓到」—— 用户看到的「卡了一下就自己重新拉起」就是这里。重启本身很轻
# （换线程 + 重新找窗口 + 清限频状态），而且画面陈旧期间调用方本来就不做判断
# （is_stale），所以随时可以重启，不会误点。
HARD_RESTART_AFTER_FAILURES = 10

# 两次「彻底重启」之间的最小间隔（秒）：重启没修好就指数退避，最长
# HARD_RESTART_MAX_INTERVAL 秒，避免故障一直存在时每 30s 就换一次线程。
HARD_RESTART_INTERVAL = 15.0
HARD_RESTART_MAX_INTERVAL = 300.0

# 截图线程多久没有心跳就认为它**卡死在系统调用里**了（PrintWindow 对没响应的
# 窗口能阻塞好几秒甚至无限期，GetDC/BitBlt 在会话被切走时也可能不返回）。
# Python 侧没有任何办法打断这种调用，唯一有效的手段是「放弃旧线程、起一个新
# 线程」—— 这件事由看门狗线程（ScreenshotWatchdog）负责。
LOOP_HANG_TIMEOUT = 20.0

# 看门狗轮询间隔（秒）
WATCHDOG_INTERVAL = 1.0

# 「真人」多久没碰键鼠，才允许把游戏窗口抢回前台（秒）。用户正在用电脑时抢
# 焦点非常讨厌，所以先等着；他一停下自愈就会把游戏窗口弄回来，任务自动继续
# （真实用户空闲时间见 real_user_idle，不会被我们自己注入的空输入骗到）。
RECOVER_MIN_USER_IDLE = 60.0

# 运行中每隔多少秒注入一次「空输入」，防止显示器休眠 / 屏保 / 自动锁屏。
# 自动化点击走的是 PostMessage + SetCursorPos，系统**不算作用户操作**，所以
# 长时间跑剧情时 Windows 会照常关屏/锁屏；一旦锁屏，DWM 不再合成用户桌面，
# PrintWindow 就彻底抓不到 D3D 画面了（现象：跑一段时间后突然一直报
# 「PrintWindow函数截取窗口图像失败」，退化的 PW_CLIENTONLY 还给一张纯黑图，
# 而重新开关任务/动一下鼠标又好了）。设为 0 可以关掉这个保活。
WAKE_INTERVAL = 20.0

# SetThreadExecutionState 的常量（申请「别关屏/别休眠」）
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# SystemParametersInfo 的常量（临时禁/启用屏保）
SPI_GETSCREENSAVEACTIVE = 0x0010
SPI_SETSCREENSAVEACTIVE = 0x0011

# ES_DISPLAY_REQUIRED 只能挡住「关屏/睡眠」，挡不住用户自己设的屏保；而屏保
# 一旦勾了「恢复时显示登录屏幕」，会话照样会锁（锁了 DWM 就不合成用户桌面，
# PrintWindow 立刻全失败）。如果 tool/capture_diagnose.py 的诊断显示屏保才是
# 罪魁，把这里改成 True：截图期间临时禁用屏保，停止时恢复成原来的设置。
# 默认关 —— 不擅自改用户的系统设置。
SUPPRESS_SCREENSAVER = False

# DwmGetWindowAttribute 的 DWMWA_CLOAKED：窗口被系统隐藏（锁屏/切换用户/切虚拟桌面）
DWMWA_CLOAKED = 14

# PrintWindow 的标志位，按顺序尝试：
#   3 = PW_CLIENTONLY | PW_RENDERFULLCONTENT（Win8.1+，能抓到 D3D 游戏内容）
#   1 = PW_CLIENTONLY（老办法，部分机器/驱动上前者会失败而它仍然可用）
# 两者都是「客户区原点」，抓出来的图依然和 2560x1440 的模板坐标对齐。
_PRINT_FLAGS = (
    (3, 'PW_RENDERFULLCONTENT'),
    (1, 'PW_CLIENTONLY'),
)

# PrintWindow 全失败时，是否允许退化成「抓屏幕」。
# 这是崩铁「全屏」模式的救命通道：全屏游戏在前台时，DWM 会走 direct-flip
# 不再合成这个窗口，PrintWindow 的所有 flag 都返回 0/纯黑（实测 0/1/2/3 全废），
# 而且这时**从窗口 DC 拷也是纯黑**（flip 的内容根本不在窗口 DC 里），
# 必须从**屏幕 DC**（GetDC(0)）拷贝窗口客户区所在的那块屏幕 —— 实测是
# 真画面（均值 65、唯一色 36 万，模板匹配 0.66~0.75）。
# 只有「屏幕上采样点确实都是这个窗口」时才用，否则会拷到盖在上面的窗口。
BITBLT_FALLBACK = True

# 抓屏幕要求的最低「可见采样命中率」（见 _window_visible_ratio）。
# 5x5 = 25 个采样点，允许最多 5 个点被别人盖住（小悬浮窗/通知），再多就认为
# 窗口已经被压住了：宁可这一帧不要，也不要把别人的像素当成游戏画面去点。
BITBLT_MIN_VISIBLE_RATIO = 0.8

# BitBlt 的图案运算码
_SRCCOPY = 0x00CC0020
_CAPTUREBLT = 0x40000000

# SetProcessDPIAware 只需要调一次，别每帧都调
_dpi_aware = False


# ---------------------------------------------------------------------------
# 限频日志 / 画面有效性判断
# ---------------------------------------------------------------------------

_log_lock = threading.Lock()
_log_last = {}


def log_throttled(key, message, interval=FAIL_LOG_INTERVAL):
    """限频打印日志：同一个 ``key`` 每 ``interval`` 秒最多出一条。

    截图失败时 PrintWindow 会连续失败（每帧一次），如果每次都 ``log`` 一下，
    日志本身就是刷屏源 —— 用户看到的「持续报错」有一半是它。所以按 key 限频。

    :return: 本次是否真的打印了
    """
    now = time.time()
    with _log_lock:
        if now - _log_last.get(key, 0.0) < interval:
            return False
        _log_last[key] = now
    log(message)
    return True


def _print_window(hwnd, hdc, flags):
    """调用 user32.PrintWindow（单独包一层，方便单测替换）。"""
    return windll.user32.PrintWindow(hwnd, hdc, flags) == 1


def _flush_gdi():
    """把挂起的 GDI 批次刷掉（重启截图线程前调用）。

    GDI 调用在进程里是**批量排队**执行的，一个卡住的 BitBlt/PrintWindow 后面
    可能还压着一串没提交的绘图命令。真正卡死的时候这些命令只能等系统回收，
    但正常情况下 GdiFlush 能把队列排空，让新起的截图线程拿到干净的 DC 状态。
    """
    try:
        return bool(windll.gdi32.GdiFlush())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 环境诊断 / 保活（「跑很久之后突然抓不到画面」的元凶就在这里）
# ---------------------------------------------------------------------------

class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]


def idle_seconds():
    """距上次「真实用户输入」过了多少秒（拿不到时返回 None）。

    自动化点击/按键走的是 ``PostMessage`` + ``SetCursorPos``，系统**不把它
    算作用户操作**，所以长时间跑剧情时这个值会一直涨 —— 涨到屏保 / 关屏 /
    自动锁屏的时间点，DWM 就不再合成用户桌面，PrintWindow 直接抓不到画面。
    """
    try:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        return (windll.kernel32.GetTickCount() - info.dwTime) / 1000.0
    except Exception:
        return None


def input_desktop_locked():
    """屏幕是不是被锁住了 / 会话被切走（锁屏时取不到输入桌面）。"""
    try:
        hdesk = windll.user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
        if not hdesk:
            return True
        windll.user32.CloseDesktop(hdesk)
        return False
    except Exception:
        return False


def window_state(hwnd):
    """窗口当前状态的人话描述，截图失败时用来定位到底是哪一种情况。"""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return '窗口句柄已失效（游戏重启/窗口被重建）'
        facts = []
        if win32gui.IsIconic(hwnd):
            facts.append('窗口已最小化')
        if not win32gui.IsWindowVisible(hwnd):
            facts.append('窗口不可见')
        try:
            cloaked = ctypes.c_int(0)
            windll.dwmapi.DwmGetWindowAttribute(
                hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
            if cloaked.value:
                facts.append('窗口被系统隐藏(cloaked：锁屏/切换用户/切虚拟桌面)')
        except Exception:
            pass
        try:
            if windll.user32.IsHungAppWindow(hwnd):
                facts.append('窗口没有响应（游戏卡住或正在加载）')
        except Exception:
            pass
        if input_desktop_locked():
            facts.append('输入桌面不可用（屏幕已锁定/切换用户）')
        ratio = _window_visible_ratio(hwnd)
        if ratio < 1.0:
            facts.append(f'屏幕上只有 {ratio:.0%} 的采样点是它'
                         f'（盖在上面的是 {_covering_window(hwnd)}）')
        idle = real_user_idle()
        if idle is not None:
            facts.append(f'距上次真实用户输入 {idle:.0f}s')
        if not facts:
            facts.append('窗口状态正常（抓不到画面前后都是显卡/驱动/DWM 层面的问题）')
        return '；'.join(facts)
    except Exception as e:
        return f'窗口状态查询异常({e})'


def keep_awake():
    """注入一次「空鼠标移动」，把系统的空闲计时器顶掉。

    这是「跑很久之后突然抓不到画面」的预防措施：只要注入成功，屏保 / 关屏 /
    自动锁屏就不会启动，DWM 也就不会停止合成用户桌面。不会移动光标，也不会
    产生点击。
    """
    try:
        windll.user32.mouse_event(1, 0, 0, 0, 0)      # MOUSEEVENTF_MOVE, dx=dy=0
        return True
    except Exception:
        return False


# 我们自己注入的输入（keep_awake 的空移动、_bring_to_front 的 ALT 空按）也会
# 顶掉系统的空闲计时器，GetLastInputInfo 就分不清「真人」和「机器人」了。
# 所以每次注入前后各记一笔，:func:`real_user_idle` 用它把这段折掉。
_inject_lock = threading.Lock()
_inject_at = 0.0          # 最近一次注入**结束**的时刻
_idle_at_inject = None    # 那次注入**之前**的真实空闲时间


def _inject_began():
    """注入输入**之前**调用：记下注入前的真实空闲时间。"""
    global _idle_at_inject
    with _inject_lock:
        _idle_at_inject = idle_seconds()


def _inject_ended():
    """注入输入**之后**调用：记下注入结束时刻（必须在之后，见 real_user_idle）。"""
    global _inject_at
    with _inject_lock:
        _inject_at = time.time()


def real_user_idle():
    """「真人」最后一次操作距离现在多少秒（扣掉本模块自己注入的输入）。

    自动化判断「用户是不是正在用电脑」必须看这个值：用 idle_seconds 会把自己
    注入的空输入也算成用户操作，结论永远是「刚刚有操作」。

    判断依据：系统记的「最后一次输入」如果早于我们那次注入的结束时刻，说明
    最后这次输入就是我们自己注入的；晚于它才是真人又动了键鼠。
    """
    idle = idle_seconds()
    with _inject_lock:
        inject_at, idle_at_inject = _inject_at, _idle_at_inject
    if idle is None:
        return None
    if not inject_at:
        return idle
    elapsed = time.time() - inject_at
    if idle < elapsed - 0.2:
        return idle                  # 注入之后又来了新输入：是真人
    if idle_at_inject is None:
        return idle
    return idle_at_inject + elapsed  # 最后一次输入正是我们注入的那次


def set_display_awake(on):
    """申请 / 释放「别关屏、别让系统休眠」（截图线程退出时会自动失效）。"""
    try:
        if on:
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        else:
            flags = ES_CONTINUOUS
        windll.kernel32.SetThreadExecutionState(flags)
        return True
    except Exception:
        return False


def screensaver_enabled():
    """用户的屏保当前是不是启用状态（拿不到时返回 None）。"""
    try:
        active = ctypes.c_int(0)
        ok = windll.user32.SystemParametersInfoW(
            SPI_GETSCREENSAVEACTIVE, 0, ctypes.byref(active), 0)
        return bool(active.value) if ok else None
    except Exception:
        return None


def set_screensaver_active(active):
    """启用 / 禁用屏保（只在 SUPPRESS_SCREENSAVER 打开时用，停止截图时会还原）。"""
    try:
        return bool(windll.user32.SystemParametersInfoW(
            SPI_SETSCREENSAVEACTIVE, 1 if active else 0, None, 0))
    except Exception:
        return False


def _read_bitmap(saveBitMap):
    """把 win32ui 位图读成 BGR 的 ndarray。"""
    bmp_info = saveBitMap.GetInfo()              # 位图信息
    bmp_str = saveBitMap.GetBitmapBits(True)     # 位图数据
    im = np.frombuffer(bmp_str, dtype='uint8')
    # GetBitmapBits 返回的是只读 buffer，copy 一份才能被 cv2 安全使用
    im = im.reshape(bmp_info['bmHeight'], bmp_info['bmWidth'], 4).copy()
    return im[:, :, :3]                          # 去掉 alpha，保留 BGR


def _is_blank(im):
    """整幅画面是不是同一个颜色（全黑之类）。

    窗口被最小化、或者画面被系统丢掉的时候，PrintWindow 会「成功地」返回一张
    纯色图。这种画面拿去模板匹配只会永远匹配不到 —— 表现就是「功能失效、
    什么都不点」，但日志里又没有报错，非常难查。所以直接当成失败处理。
    """
    if im is None or im.size == 0:
        return True
    sample = im[::32, ::32]                      # 抽样即可，别整幅比较
    return bool(sample.min() == sample.max())


def _grab_into_bitmap(hwnd, hdc, saveBitMap):
    """把一帧窗口画面抓进 ``saveBitMap``，返回 ``(图像, 失败原因)``。

    依次尝试 :data:`_PRINT_FLAGS` 里的两种 PrintWindow；第一种是抓 D3D 游戏
    内容用的，失败时降级到第二种（原实现只试第一种，一失败就整帧丢弃）。
    """
    reasons = []
    for flags, name in _PRINT_FLAGS:
        try:
            ok = _print_window(hwnd, hdc, flags)
        except Exception as e:
            ok = False
            reasons.append(f'{name} 调用异常({e})')
        if not ok:
            reasons.append(f'{name} 返回失败')
            continue
        im = _read_bitmap(saveBitMap)
        if _is_blank(im):
            reasons.append(f'{name} 抓到纯色/全黑画面')
            continue
        return im, None

    try:
        if ctypes_is_hung(hwnd):
            reasons.append('窗口没有响应（游戏卡住或正在加载）')
    except Exception:
        pass
    return None, 'PrintWindow函数截取窗口图像失败：' + '；'.join(reasons)


def ctypes_is_hung(hwnd):
    """窗口是不是「未响应」（IsHungAppWindow；pywin32 没包这个 API）。"""
    return bool(windll.user32.IsHungAppWindow(hwnd))


def _foreground_is(hwnd):
    """目标窗口是不是当前的前台窗口（只用于日志描述，**不要**拿它当抓图闸门）。

    切换窗口的那一瞬间，前台会变成系统内部窗口（ForegroundStaging、
    任务切换的 MultitaskingViewFrame……），实测 4 秒能跳 249 次；用它当闸门
    会把本来能抓到的画面丢掉。真正的闸门是 :func:`_window_visible_ratio`。
    """
    try:
        return win32gui.GetForegroundWindow() == hwnd
    except Exception:
        return False


def _window_label(hwnd):
    """窗口的一句话标识（``'标题'(类名)``），只用于日志。

    跨进程读标题是安全的：GetWindowText 对别的进程不会发 WM_GETTEXT，不会卡住；
    但**本进程**的窗口会（要走自己的消息循环），所以本进程只取类名。
    """
    try:
        cls = win32gui.GetClassName(hwnd) or '?'
    except Exception:
        cls = '?'
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == win32api.GetCurrentProcessId():
            return cls
    except Exception:
        pass
    try:
        title = win32gui.GetWindowText(hwnd)
    except Exception:
        title = ''
    return f'{title!r}({cls})' if title else cls


def _window_visible_ratio(hwnd):
    """采样窗口矩形内的 25 个点，返回「屏幕上这些点确实是本窗口」的比例。

    这是抓屏幕回退的闸门。**不能用 GetForegroundWindow 做闸门**：切换窗口时
    前台会短暂变成系统内部窗口（ForegroundStaging、任务切换的
    MultitaskingViewFrame 等），刚测过 4 秒里能跳 249 次，会导致明明能抓的画面
    被误判成「不在前台」而丢掉（日志里就会一会儿好、一会儿坏）。
    WindowFromPoint 反映的是**屏幕上这个点真的是哪个窗口**，稳得多。
    """
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0:
            return 0.0
        root = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
        hit = 0
        total = 0
        for fy in (0.1, 0.3, 0.5, 0.7, 0.9):
            for fx in (0.1, 0.3, 0.5, 0.7, 0.9):
                total += 1
                point = (int(left + width * fx), int(top + height * fy))
                try:
                    under = win32gui.WindowFromPoint(point)
                except Exception:
                    continue
                if not under:
                    continue
                if under == hwnd:
                    hit += 1
                    continue
                try:
                    if win32gui.GetAncestor(under, win32con.GA_ROOT) == root:
                        hit += 1
                except Exception:
                    pass
        return hit / total if total else 0.0
    except Exception:
        return 0.0


def _covering_window(hwnd):
    """屏幕上盖住目标窗口（中心点那个）的窗口标识，用来说清楚「到底是谁挡住了」。"""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        under = win32gui.WindowFromPoint(((left + right) // 2, (top + bottom) // 2))
        if not under:
            return '桌面'
        if under == hwnd or win32gui.GetAncestor(under, win32con.GA_ROOT) == hwnd:
            return '无（是本窗口自己）'
        root = win32gui.GetAncestor(under, win32con.GA_ROOT) or under
        return _window_label(root)
    except Exception:
        return '?'


def _fullscreen_window(hwnd):
    """窗口是不是「全屏」的（无边框 popup 且基本盖满所在显示器）。"""
    try:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if style & win32con.WS_CAPTION:
            return False
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        monitor = win32api.MonitorFromWindow(hwnd, 2)      # NEAREST
        info = win32api.GetMonitorInfo(monitor)
        m_left, m_top, m_right, m_bottom = info['Monitor']
        return ((right - left) >= (m_right - m_left) * 0.95
                and (bottom - top) >= (m_bottom - m_top) * 0.95)
    except Exception:
        return False


def _wait_foreground(hwnd, timeout=0.6):
    """等窗口真的成为前台窗口（SetForegroundWindow 是异步生效的）。"""
    end = time.time() + timeout
    while time.time() < end:
        if _foreground_is(hwnd):
            return True
        time.sleep(0.02)
    return _foreground_is(hwnd)


def _bring_to_front(hwnd):
    """把窗口还原并抢到最前面，返回是否真的成了前台窗口。

    为什么这么绕：Windows 只允许「当前拥有输入焦点、或刚收到过输入的进程」
    调用 SetForegroundWindow，后台进程的调用会被**静默忽略**（不抛异常，只是
    什么都没发生 —— 所以以前「抢回前台」看起来执行了却没效果）。所以依次：
    发一次 ALT 空按（让系统认为最后输入来自本进程）-> SetForegroundWindow
    -> 仍不行就挂到前台窗口线程上再来一次 -> 最后挂目标线程 BringWindowToTop。
    """
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    if _foreground_is(hwnd):
        return True

    # 1) ALT 空按 + SetForegroundWindow（最常见、最有效）
    _inject_began()
    try:
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    finally:
        _inject_ended()
    if _wait_foreground(hwnd):
        return True

    # 2) 前台锁在前台窗口所在线程手里：挂上去再设，然后挂到目标线程兜底
    try:
        current = windll.kernel32.GetCurrentThreadId()
    except Exception:
        return False
    for other in (win32gui.GetForegroundWindow(), hwnd):
        try:
            tid, _pid = win32process.GetWindowThreadProcessId(other)
        except Exception:
            continue
        if not tid or tid == current:
            continue
        try:
            windll.user32.AttachThreadInput(current, tid, True)
            try:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetForegroundWindow(hwnd)
            finally:
                windll.user32.AttachThreadInput(current, tid, False)
        except Exception:
            pass
        if _wait_foreground(hwnd):
            return True
    return False


def _recover_hint():
    """抢前台失败时给用户看的建议（窗口化模式下根本不需要抢前台）。"""
    return ('如果希望后台也能截图：把崩铁改成「窗口化」模式，窗口模式下 DWM 会'
            '正常合成这个窗口，PrintWindow 即使游戏不在前台也能抓到画面')


def _bitblt_into_bitmap(hwnd, dest_hdc, saveBitMap, width, height):
    """退路抓图：从**屏幕 DC** 拷贝窗口客户区所在的那块屏幕，返回 ``(图像, 原因)``。

    为什么需要它：崩铁「全屏」时窗口是 popup 且盖满整个屏幕，一旦它成为前台
    窗口，DWM 就会走 direct-flip（不再合成这个窗口）。实测此时
    PrintWindow 的 0/1/2/3 四种 flag **全部返回 0**，DwmFlush 也没用；
    **从窗口 DC（GetWindowDC）BitBlt 同样是一张纯黑图** —— flip 的内容压根不在
    窗口 DC 里。唯一能拿到画面的是**屏幕 DC**（GetDC(0)），实测均值 65、
    唯一色 36 万，模板匹配 0.66~0.75。

    **只在「屏幕上这些点确实是本窗口」时才允许**（见 _window_visible_ratio）：
    窗口被别的窗口盖住时，拷到的会是上层的像素，被当成游戏画面就会乱点。
    """
    if not BITBLT_FALLBACK:
        return None, '抓屏幕回退已关闭'
    ratio = _window_visible_ratio(hwnd)
    if ratio < BITBLT_MIN_VISIBLE_RATIO:
        return None, (f'窗口在屏幕上不可见（采样命中 {ratio:.0%}，'
                      f'盖在上面的是 {_covering_window(hwnd)}；'
                      f'抓屏幕只会拷到上层窗口的像素）')
    try:
        # 客户区在屏幕上的左上角（进程已 SetProcessDPIAware，坐标是物理像素）
        origin = win32gui.ClientToScreen(hwnd, (0, 0))
    except Exception as e:
        return None, f'算不出客户区在屏幕上的位置({e})'
    screen_dc = None
    try:
        screen_dc = win32gui.GetDC(0)
        if not screen_dc:
            return None, '拿不到屏幕 DC'
        ok = windll.gdi32.BitBlt(dest_hdc, 0, 0, width, height, screen_dc,
                                 origin[0], origin[1], _SRCCOPY | _CAPTUREBLT)
    except Exception as e:
        return None, f'抓屏幕调用异常({e})'
    finally:
        if screen_dc:
            try:
                win32gui.ReleaseDC(0, screen_dc)
            except Exception:
                pass
    if not ok:
        return None, '抓屏幕返回失败'
    im = _read_bitmap(saveBitMap)
    if _is_blank(im):
        return None, '抓屏幕抓到纯色/全黑画面'
    return im, None


# ---------------------------------------------------------------------------
# 底层单次截图
# ---------------------------------------------------------------------------

def capture_hwnd(hwnd):
    """截取指定窗口句柄的客户区画面，返回 BGR 的 ndarray（失败返回 None）。"""
    global _dpi_aware
    if not hwnd:
        return None
    hwndDC = saveDC = mfcDC = saveBitMap = old_bitmap = None
    try:
        if not _dpi_aware:
            windll.user32.SetProcessDPIAware()
            _dpi_aware = True
        sp_left, sp_top, sp_right, sp_bot = win32gui.GetClientRect(hwnd)
        real_sp_w = int(sp_right - sp_left)
        real_sp_h = int(sp_bot - sp_top)
        if real_sp_w <= 0 or real_sp_h <= 0:
            # 窗口最小化 / 被隐藏时客户区就是 0x0。这里也必须说清楚，否则表现
            # 成「画面不再更新，但一条日志都没有」—— 这是最难查的一种。
            log_throttled(
                'capture_empty',
                f'窗口客户区是 {real_sp_w}x{real_sp_h}，取不到画面。'
                f'窗口状态：{window_state(hwnd)}',
            )
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)           # 窗口设备上下文（DC）
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)    # 由 hwndDC 创建 MFC DC
        saveDC = mfcDC.CreateCompatibleDC()           # 创建兼容 DC
        saveBitMap = win32ui.CreateBitmap()           # 创建位图对象
        saveBitMap.CreateCompatibleBitmap(mfcDC, real_sp_w, real_sp_h)
        old_bitmap = saveDC.SelectObject(saveBitMap)  # 选入位图，准备绘图

        im, reason = _grab_into_bitmap(hwnd, saveDC.GetSafeHdc(), saveBitMap)
        if im is None:
            # PrintWindow 全挂（最常见：全屏游戏在前台，DWM 走 direct-flip 不再
            # 合成该窗口）时，退一步直接抓屏幕。见 _bitblt_into_bitmap
            im, shot_reason = _bitblt_into_bitmap(
                hwnd, saveDC.GetSafeHdc(), saveBitMap, real_sp_w, real_sp_h)
            if im is None:
                log_throttled(
                    'capture_fail',
                    f'{reason}；{shot_reason}（客户区 {real_sp_w}x{real_sp_h}）。'
                    f'窗口状态：{window_state(hwnd)}',
                )
                return None
            log_throttled(
                'capture_bitblt',
                f'PrintWindow 抓不到画面（{reason}），已改用抓屏幕'
                f'（全屏游戏在前台时 DWM 不再合成它，只有屏幕 DC 能拿到画面）',
                interval=60,
            )

        if setting.get('resolution') != [2560, 1440]:
            im = cv2.resize(im, (2560, 1440), interpolation=cv2.INTER_AREA)
        return im
    except Exception as e:
        log_throttled('capture_exc', f'截图异常: {e}')
        return None
    finally:
        # 必须释放 GDI 资源，否则长时间循环运行会句柄泄漏
        try:
            if saveDC is not None and old_bitmap is not None:
                # 先把位图从 DC 里换出来，DeleteObject 才真的释放它
                # （位图还选在 DC 里时是删不掉的 -> 每帧泄漏一张 8MB 位图）
                saveDC.SelectObject(old_bitmap)
        except Exception:
            pass
        try:
            if saveBitMap is not None:
                win32gui.DeleteObject(saveBitMap.GetHandle())
        except Exception:
            pass
        for dc in (saveDC, mfcDC):
            try:
                if dc is not None:
                    dc.DeleteDC()
            except Exception:
                pass
        try:
            if hwndDC is not None:
                win32gui.ReleaseDC(hwnd, hwndDC)
        except Exception:
            pass


def capture_window(window_title):
    """按窗口标题单次截图（保持原 ``func.get_pic.get_pic`` 的行为）。"""
    hwnd = get_hwnd(window_title)
    if not hwnd:
        log(f"Window with title '{window_title}' not found.", level=2)
        return None
    return capture_hwnd(hwnd)


# ---------------------------------------------------------------------------
# 循环截图服务
# ---------------------------------------------------------------------------

class ScreenshotService:
    """后台循环截图服务（进程内单例，见文件末尾的 ``service``）。"""

    def __init__(self):
        self._thread = None
        self._stop_event = None
        self._frame = None          # 最新一帧，只整体替换，不原地修改
        self._window_title = None
        self._interval = DEFAULT_INTERVAL
        self._hwnd = None
        self._fail_count = 0
        self._last_resolve = 0.0    # 上一次按标题重新找窗口的时刻
        self._last_wake = 0.0       # 上一次「顶掉空闲计时器」的时刻
        self._last_recover = 0.0    # 上一次尝试还原/置前游戏窗口的时刻
        self._recover_fails = 0     # 自愈（还原/抢前台）连续失败的次数，用于退避
        self._recover_thread = None # 正在执行的置前动作（独立线程，免得拖死截图线程）
        self._screensaver_was = None  # 临时关屏保前的原设置（用于还原）
        self._last_frame_at = 0.0   # 最近一次真的抓到画面的时刻（判断画面「死」了多久）
        self._last_beat = 0.0       # 截图线程的心跳时刻（看门狗用它发现卡死）
        self._generation = 0        # 循环代次：「彻底重启」时 +1，旧循环退出时据此收尾
        self._active = False        # start() 之后、stop() 之前为 True（看门狗闸门）
        self._restart_count = 0     # 累计「彻底重启截图线程」的次数
        self._last_restart = 0.0    # 上一次彻底重启的时刻
        self._restart_fails = 0     # 重启之后仍然失败的次数（用于退避）
        self._watchdog = None
        self._watchdog_stop = None
        self._lock = threading.Lock()

    # -- 状态 ---------------------------------------------------------------

    @property
    def is_running(self):
        """循环截图线程是否正在运行。"""
        return self._thread is not None and self._thread.is_alive()

    @property
    def window_title(self):
        """当前正在截图的窗口标题。"""
        return self._window_title

    @property
    def interval(self):
        """当前截图间隔（秒）。"""
        return self._interval

    @property
    def fail_count(self):
        """连续截图失败的次数（成功抓一帧就清零）。"""
        return self._fail_count

    @property
    def restart_count(self):
        """本次截图会话里「彻底重启截图线程」的次数（排查用）。"""
        return self._restart_count

    @property
    def last_frame_age(self):
        """最近一次真的抓到画面到现在过了多少秒。

        从没抓到过帧时返回「本次截图开始到现在」的秒数；服务从未启动过返回
        ``inf``。调用方（GUI 的任务看护）用它判断画面是不是「已经死透了」：
        截图线程重启几次都还没帧，说明是进程级的 GDI/DWM 状态坏了，只能重开
        任务进程。
        """
        if not self._last_frame_at:
            return float('inf')
        return max(0.0, time.time() - self._last_frame_at)

    @property
    def stale(self):
        """画面是不是已经「陈旧」（截图连续失败、最新一帧不再更新）。

        调用方在拿 ``latest()`` 的画面做判断前可以先问一下：陈旧时应当只等待，
        **不要**继续按旧画面点击 —— 否则会对着过期界面乱点（表现就是
        「功能失效 / 乱点」），还会把游戏窗口的消息队列刷爆、让它更卡。
        """
        return self._fail_count >= STALE_AFTER_FAILURES

    def set_interval(self, interval):
        """动态调整截图间隔（供任务运行时临时降频，<=0 忽略）。"""
        if interval and interval > 0:
            self._interval = interval

    # -- 生命周期 -----------------------------------------------------------

    def start(self, window_title, interval=DEFAULT_INTERVAL):
        """启动（或切换窗口）循环截图。

        重复调用同一窗口不会重启线程，可以安全地在每个任务开头调用。
        """
        with self._lock:
            if self.is_running and self._window_title == window_title:
                if interval and interval > 0:
                    self._interval = interval
                return
            self._stop_locked()

            self._window_title = window_title
            self._interval = interval if interval and interval > 0 else DEFAULT_INTERVAL
            self._frame = None
            self._fail_count = 0
            self._last_resolve = 0.0
            self._last_wake = 0.0
            self._last_recover = 0.0
            self._recover_fails = 0
            self._recover_thread = None
            self._last_frame_at = time.time()   # 本次会话「从什么时候开始等画面」
            self._restart_count = 0
            self._last_restart = 0.0
            self._restart_fails = 0
            self._active = True
            self._resolve_hwnd(force=True)
            self._generation += 1
            self._stop_event = threading.Event()
            self._last_beat = time.time()
            self._thread = threading.Thread(
                target=self._loop, args=(self._generation, self._stop_event),
                name='ScreenshotLoop', daemon=True
            )
            self._thread.start()
            self._start_watchdog()
            log(f'通用截图服务已启动: {window_title} (间隔 {self._interval}s)')

    def stop(self, timeout=2):
        """停止循环截图。最后一帧会保留，便于调用方继续读取。"""
        with self._lock:
            self._stop_locked(timeout)

    def _stop_locked(self, timeout=2):
        # 先把看门狗关掉：否则它看到「线程不在」会立刻又拉起一个，stop 就失效了
        self._active = False
        self._stop_watchdog()
        thread = self._thread
        if thread is None:
            return
        stop_event = self._stop_event
        self._thread = None
        self._stop_event = None
        self._hwnd = None
        if stop_event is not None:
            stop_event.set()
        if thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout)
        log('通用截图服务已停止')

    def _start_watchdog(self):
        """起看门狗线程（已经在跑就不重复起）。"""
        if self._watchdog is not None and self._watchdog.is_alive():
            return
        self._watchdog_stop = threading.Event()
        self._watchdog = threading.Thread(
            target=self._watchdog_loop, name='ScreenshotWatchdog', daemon=True,
        )
        self._watchdog.start()

    def _stop_watchdog(self, timeout=0.5):
        stop_event = self._watchdog_stop
        watchdog = self._watchdog
        self._watchdog = None
        self._watchdog_stop = None
        if stop_event is not None:
            stop_event.set()
        if (watchdog is not None and watchdog.is_alive()
                and watchdog is not threading.current_thread()):
            watchdog.join(timeout)

    def _watchdog_loop(self):
        """看门狗：截图线程死了 / 卡死了 / 一直抓不到画面 -> 彻底重启它。"""
        stop_event = self._watchdog_stop
        while stop_event is not None and not stop_event.wait(WATCHDOG_INTERVAL):
            try:
                self._watchdog_tick(stop_event)
            except Exception as e:
                log_throttled('watchdog_exc', f'截图看门狗检查异常：{e}', interval=30)

    def _watchdog_tick(self, stop_event=None):
        """看门狗的一次检查。"""
        if not self._active:
            return
        if stop_event is not None and stop_event is not self._watchdog_stop:
            return                      # 这个看门狗已经被 stop()/start() 换掉了
        reason = None
        if not self.is_running:
            # 线程被 PrintWindow 之外的异常/系统回收带走了：重新起一个
            reason = '截图线程已经退出（异常退出或被系统回收）'
        else:
            hang = time.time() - self._last_beat
            if hang >= LOOP_HANG_TIMEOUT:
                reason = (f'截图线程 {hang:.0f}s 没有心跳，判定卡在 '
                          f'PrintWindow/GetDC 之类的系统调用里')
            elif self._fail_count >= HARD_RESTART_AFTER_FAILURES:
                reason = f'连续 {self._fail_count} 次抓不到画面'
        if reason is None:
            return
        # 重启没修好就指数退避：故障一直存在时每 30s 换一次线程只会更糟
        # （每次都要重新枚举窗口、重新拿 DC），退到 HARD_RESTART_MAX_INTERVAL 封顶。
        interval = min(HARD_RESTART_INTERVAL * (2 ** min(self._restart_fails, 6)),
                       HARD_RESTART_MAX_INTERVAL)
        if time.time() - self._last_restart < interval:
            return
        self._restart_fails += 1
        self.restart(reason, watchdog=stop_event)

    # -- 彻底重启 -----------------------------------------------------------

    def restart(self, reason='手动重启', watchdog=None):
        """彻底重启截图线程（「杀掉旧线程，重新拉起一个新线程」）。

        为什么需要它：截图线程一旦卡在 ``PrintWindow`` / ``GetDC`` / ``BitBlt``
        这类**系统调用**里，Python 侧没有任何办法把它打断（GIL 早就释放了，只能
        等调用返回）；表现就是画面永远不再更新、``is_stale()`` 一直为真，怎么等
        都不会自己好。这时唯一有效的手段是放弃这个线程、换一个新的：新线程会
        重新按标题找窗口、重新拿 DC，卡住的那个是 daemon 线程，进程退出时一起
        回收（正常情况下它会在这之前自己醒来并退出）。

        :param reason: 重启原因（写进日志，便于事后判断是哪种故障）
        :param watchdog: 内部用：发起调用的看门狗标识（防止被换掉的看门狗插手）
        :return: 是否真的重启了（服务没在运行 / 已停止时返回 False）
        """
        with self._lock:
            if watchdog is not None and watchdog is not self._watchdog_stop:
                return False            # 调用者是个已经被换掉的看门狗，忽略
            return self._restart_locked(reason)

    def _restart_locked(self, reason):
        if not self._active:
            return False
        _flush_gdi()                     # 把挂起的 GDI 批次刷掉，别带给新线程
        old_thread = self._thread
        old_stop = self._stop_event
        if old_stop is not None:
            old_stop.set()
        if (old_thread is not None and old_thread.is_alive()
                and old_thread is not threading.current_thread()):
            # 正常情况 stop_event 一置位它就退出；真卡在系统调用里就只能放弃
            old_thread.join(1.0)
        stuck = old_thread is not None and old_thread.is_alive()

        self._hwnd = None                # 句柄重新按标题找（游戏可能重启过）
        self._fail_count = STALE_AFTER_FAILURES   # 立刻标陈旧：别让调用方用旧画面
        self._last_resolve = 0.0
        self._recover_fails = 0
        self._last_recover = 0.0
        self._restart_count += 1
        self._last_restart = time.time()
        _log_last.clear()                # 让新的失败原因能立刻打出来（清限频状态）
        self._resolve_hwnd(force=True)

        self._generation += 1
        self._stop_event = threading.Event()
        self._last_beat = time.time()
        self._thread = threading.Thread(
            target=self._loop, args=(self._generation, self._stop_event),
            name=f'ScreenshotLoop#{self._restart_count + 1}', daemon=True,
        )
        self._thread.start()
        log(f'已杀掉截图线程（第 {self._restart_count} 次），正在重新拉起：{reason}；'
            f'{"旧线程卡死在里面，已放弃" if stuck else "旧线程已退出"}，'
            f'重新找窗口、重新抓画面')
        return True

    # -- 读取 ---------------------------------------------------------------

    def latest(self, window_title=None):
        """返回最新一帧（零拷贝，未启动或无画面时返回 None）。

        ``window_title`` 与当前截图窗口不一致时也返回 None，避免把原神的
        画面当成星铁的画面误用。
        """
        frame = self._frame
        if frame is None:
            return None
        if window_title is not None and self._window_title != window_title:
            return None
        return frame

    # -- 循环 ---------------------------------------------------------------

    def _loop(self, generation, stop_event):
        # generation：循环代次。「彻底重启」时 +1，旧循环（可能是卡死后被放弃
        # 的那个）醒来退出时据此判断「我已经不是当前循环了」，不去撤新循环的
        # 保活 / 屏保状态。
        # 截图期间申请「别关屏、别休眠」：自动化点击走 PostMessage，系统不算
        # 用户操作，长时间跑剧情必然触发关屏/屏保 —— 一旦锁屏 DWM 就不再合成
        # 用户桌面，PrintWindow 会一直失败（见 keep_awake 注释）。线程结束/进程
        # 退出时这个申请自动失效，不会影响用户后续使用。
        set_display_awake(True)
        if SUPPRESS_SCREENSAVER and self._screensaver_was is None:
            # 可选：截图期间临时关掉屏保（停止时还原），见 SUPPRESS_SCREENSAVER
            self._screensaver_was = screensaver_enabled()
            if self._screensaver_was:
                set_screensaver_active(False)
                log('已临时关闭屏保（SUPPRESS_SCREENSAVER=True），停止截图时会还原')
        while not stop_event.is_set():
            began = time.time()
            # 心跳：卡在 PrintWindow/GetDC 里时这里就不动了，看门狗据此重启线程
            self._last_beat = began
            self._keep_alive()
            frame = self._grab()
            if generation != self._generation:
                break       # 已被「彻底重启」换掉：别再写心跳 / 画面 / 计数
            self._last_beat = time.time()
            interval = self._interval
            if frame is not None:
                self._frame = frame        # 原子替换，绝不原地修改
                self._last_frame_at = time.time()
                self._fail_count = 0
                self._recover_fails = 0    # 画面回来了，自愈的退避也重置
                self._restart_fails = 0    # 彻底重启的退避也重置
            else:
                self._fail_count += 1
                # 一直失败通常是窗口被最小化 / 被遮挡，或者游戏没响应：这时候
                # 继续按 DEFAULT_INTERVAL（10~50ms）高频重试，只会把它本来就
                # 卡住的消息队列刷得更满（越刷越卡）。所以失败期间降频重试，
                # 抓到一帧后自动回到正常频率。
                interval = max(interval, FAIL_RETRY_INTERVAL)
                if self._fail_count == STALE_AFTER_FAILURES:
                    log(f'截图已连续失败 {self._fail_count} 次，画面停止更新'
                        f'（{self._window_title}）：改成每 {FAIL_RETRY_INTERVAL:g}s '
                        f'重试一次，期间调用方应停止使用旧画面')
                self._resolve_hwnd()        # 窗口可能重启了（限频，最多 3s 一次）
                self._try_recover_window()  # 被最小化就主动还原（限频 15s 一次）

            spare = interval - (time.time() - began)
            if spare > 0:
                # 用 wait 而不是 sleep，停止时能立即退出，不会卡住 timeout
                stop_event.wait(spare)
        if generation != self._generation:
            # 已经被「彻底重启」换掉了：保活 / 屏保是**新循环**在管，别乱撤
            return
        set_display_awake(False)
        if SUPPRESS_SCREENSAVER and self._screensaver_was:
            set_screensaver_active(True)      # 还原用户的屏保设置
            self._screensaver_was = None

    def _keep_alive(self):
        """定时顶掉系统的空闲计时器，别让屏保/关屏/自动锁屏打断长时间任务。"""
        if not WAKE_INTERVAL:
            return
        now = time.time()
        if now - self._last_wake < WAKE_INTERVAL:
            return
        self._last_wake = now
        idle = real_user_idle()
        _inject_began()                # 先记下「注入前」的真实空闲时间
        try:
            keep_awake()
        finally:
            _inject_ended()            # 再记下注入结束时刻（real_user_idle 要用）
        if idle is not None and idle >= WAKE_INTERVAL - 1:
            # 只在「确实已经空闲很久」时说一句，正常使用时不会刷屏
            log_throttled('capture_awake',
                          f'已空闲 {idle:.0f}s，注入一次空输入防止屏保/关屏/锁屏'
                          f'（自动化点击走 PostMessage，系统不算用户操作）',
                          interval=60)

    def _try_recover_window(self):
        """窗口最小化 / 隐藏 / 被切走时主动把它弄回屏幕，让截图能自己恢复。

        三种情况：
        * 最小化 / 不可见 -> ``SW_RESTORE``；
        * 全屏游戏被切到别的窗口后面：实测这时抓图**完全无解**（PrintWindow 的
          0/1/2/3 全返回 0，窗口 DC 抓出来纯黑，屏幕 DC 只会拷到上层窗口），
          唯一出路是把它抢回前台；
        * 用户正在用电脑（真人 60s 内有操作）就**先等着**，别抢焦点打断人家 ——
          他一停下，这里就会自动把游戏窗口弄回来，任务继续跑。

        真正的置前动作放在独立线程里：AttachThreadInput 之类万一卡住，绝不能把
        截图线程一起拖死（那正是我们要消灭的故障）。
        """
        hwnd = self._hwnd
        try:
            if not hwnd or not win32gui.IsWindow(hwnd):
                return
            hidden = win32gui.IsIconic(hwnd) or not win32gui.IsWindowVisible(hwnd)
            blocked = _window_visible_ratio(hwnd) < BITBLT_MIN_VISIBLE_RATIO
            if not (hidden or (blocked and _fullscreen_window(hwnd))):
                return
            idle = real_user_idle()
            if idle is not None and idle < RECOVER_MIN_USER_IDLE:
                log_throttled(
                    'recover_wait_user',
                    f'{self._window_title} 的画面抓不到（'
                    f'{"被最小化/隐藏" if hidden else f"被 {_covering_window(hwnd)} 挡住"}），'
                    f'但检测到你正在用电脑（{idle:.0f}s 前有操作），先不动它；'
                    f'等你停下 {RECOVER_MIN_USER_IDLE:.0f}s 后会自动把它弄回前台',
                    interval=120,
                )
                return
            now = time.time()
            interval = min(RECOVER_INTERVAL * (2 ** min(self._recover_fails, 10)),
                           RECOVER_MAX_INTERVAL)
            if now - self._last_recover < interval:
                return
            if self._recover_thread is not None and self._recover_thread.is_alive():
                return
            self._last_recover = now
            self._recover_fails += 1
            if hidden:
                log(f'{self._window_title} 窗口被最小化/隐藏了（截图抓不到画面），'
                    f'正在还原并置前')
            else:
                log(f'{self._window_title} 全屏窗口被 {_covering_window(hwnd)} 挡住了'
                    f'（屏幕上抓不到它），正在把它抢回前台让截图继续')
            self._recover_thread = threading.Thread(
                target=self._recover_now, args=(hwnd,),
                name='ScreenshotRecover', daemon=True,
            )
            self._recover_thread.start()
        except Exception as e:
            log(f'还原 {self._window_title} 窗口失败：{e}')

    def _recover_now(self, hwnd):
        """真正去抢前台（在独立线程里跑，见 _try_recover_window）。"""
        try:
            if _bring_to_front(hwnd):
                log(f'{self._window_title} 已切回前台，等截图恢复')
            else:
                log(f'没能把 {self._window_title} 切回前台（可能被系统策略阻止），'
                    f'请手动点一下游戏窗口；{_recover_hint()}')
        except Exception as e:
            log(f'还原 {self._window_title} 窗口失败：{e}')

    def _grab(self):
        if not self._hwnd or not win32gui.IsWindow(self._hwnd):
            # 句柄失效（窗口被关掉/游戏重启了）就立刻重新找，别等限频
            self._resolve_hwnd(force=True)
        if not self._hwnd:
            return None
        return capture_hwnd(self._hwnd)

    def _resolve_hwnd(self, force=False):
        """按标题重新找窗口（限频，最多每 RESOLVE_INTERVAL 秒一次）。

        原实现在**每次失败**时都重新枚举一遍所有窗口，失败期间就是 20~100Hz
        地枚举 + 跨进程读标题，纯浪费；而且一旦枚举过程被卡住，截图线程就
        再也回不来了。这里限频，同时保留「窗口重启后能重新找到」的能力。
        """
        now = time.time()
        if not force and now - self._last_resolve < RESOLVE_INTERVAL:
            return
        self._last_resolve = now
        self._hwnd = get_hwnd(self._window_title)


# 进程内单例：原神 / 崩铁 / 鸣潮所有功能模块共用
service = ScreenshotService()


# ---------------------------------------------------------------------------
# 模块级便捷函数（推荐外部只使用这几个）
# ---------------------------------------------------------------------------

def start_capture(window_title, interval=DEFAULT_INTERVAL):
    """启动全局循环截图。重复调用同一窗口是安全的。"""
    service.start(window_title, interval)


def stop_capture(timeout=2):
    """停止全局循环截图。"""
    service.stop(timeout)


def latest(window_title=None):
    """取最新一帧，没有则为 None。"""
    return service.latest(window_title)


def is_capturing():
    """全局循环截图是否正在运行。"""
    return service.is_running


def is_stale():
    """当前画面是不是「陈旧」的（截图连续失败、最新一帧不再更新）。

    check 类在拿 ``processed_screen`` 做判断 / 点击之前先问一下：陈旧时应当
    只等待截图恢复，**不要**继续按旧画面点击。否则窗口被最小化、或者游戏
    一时没响应时，会一直对着**过期的那一帧**重复点击（表现就是「功能失效、
    乱点」），还会把游戏窗口的消息队列刷爆、让整机更卡。
    """
    return service.stale


def capture_fail_count():
    """连续截图失败的次数（排查用：0 表示画面是新鲜的）。"""
    return service.fail_count


def capture_restart_count():
    """本次截图会话里「彻底重启截图线程」的次数（排查用）。"""
    return service.restart_count


def last_frame_age():
    """最近一次真的抓到画面到现在过了多少秒（从没抓到过返回 ``inf``）。"""
    return service.last_frame_age


def restart_capture(reason='手动重启'):
    """彻底重启循环截图线程：放弃旧线程（哪怕它卡死在系统调用里），换新的。

    典型场景：跑一段时间后 PrintWindow / GetDC 突然全失败、画面再也不更新
    （就是用户看到的「画面已停止更新（截图连续失败）」一直刷）。看门狗会在
    连续失败 / 卡死时自动调用它，需要手动兜底时也可以直接调。

    :return: 是否真的重启了（服务没在运行时返回 False）
    """
    return service.restart(reason)


def set_capture_interval(interval):
    """动态调整全局截图间隔（秒）。

    供 ``c.time_limit = 0.2`` 这类运行中降频的写法使用，保证老代码的
    「战斗中降低截图频率省 CPU」行为继续有效。
    """
    service.set_interval(interval)


def get_pic(window_title):
    """取一帧画面（兼容旧的 ``func.get_pic.get_pic`` 签名）。

    循环截图已启动且窗口匹配时直接返回共享帧（零拷贝、极快）；
    否则回退为单次实时截图。
    """
    if service.is_running:
        frame = service.latest(window_title)
        if frame is not None:
            return frame
    return capture_window(window_title)


def wait_first_frame(window_title, timeout=5):
    """等待循环截图产出第一帧，成功返回 True（任务启动时用）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if latest(window_title) is not None:
            return True
        time.sleep(0.05)
    return False


if __name__ == '__main__':
    title = '原神'
    start_capture(title)
    try:
        for i in range(10):
            t0 = time.time()
            frame = latest(title)
            shape = None if frame is None else frame.shape
            print(f'第 {i} 帧: {shape} 读取耗时 {time.time() - t0:.4f}s')
            time.sleep(0.1)
    finally:
        stop_capture()
