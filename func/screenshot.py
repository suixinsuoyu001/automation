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
    screenshot.stop_capture()               # 停止

    # 兼容老写法（会自动走共享缓存）
    from func.get_pic import get_pic
    frame = get_pic('原神')
"""

import threading
import time

import cv2
import numpy as np
import win32gui
import win32ui
from ctypes import windll

from func.common import get_hwnd, log, setting

# 循环截图默认间隔（秒）。原实现靠 get_pic 自身耗时来节流，这里显式给出。
DEFAULT_INTERVAL = 0.01


# ---------------------------------------------------------------------------
# 底层单次截图
# ---------------------------------------------------------------------------

def capture_hwnd(hwnd):
    """截取指定窗口句柄的客户区画面，返回 BGR 的 ndarray（失败返回 None）。"""
    if not hwnd:
        return None
    hwndDC = saveDC = mfcDC = saveBitMap = None
    try:
        windll.user32.SetProcessDPIAware()
        sp_left, sp_top, sp_right, sp_bot = win32gui.GetClientRect(hwnd)
        real_sp_w = int(sp_right - sp_left)
        real_sp_h = int(sp_bot - sp_top)
        if real_sp_w <= 0 or real_sp_h <= 0:
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)          # 窗口设备上下文（DC）
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)   # 由 hwndDC 创建 MFC DC
        saveDC = mfcDC.CreateCompatibleDC()          # 创建兼容 DC
        saveBitMap = win32ui.CreateBitmap()          # 创建位图对象
        saveBitMap.CreateCompatibleBitmap(mfcDC, real_sp_w, real_sp_h)
        saveDC.SelectObject(saveBitMap)              # 选入位图，准备绘图

        if windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3) != 1:
            log('PrintWindow函数截取窗口图像失败')
            return None

        bmp_info = saveBitMap.GetInfo()              # 位图信息
        bmp_str = saveBitMap.GetBitmapBits(True)     # 位图数据
        im = np.frombuffer(bmp_str, dtype='uint8')
        # GetBitmapBits 返回的是只读 buffer，copy 一份才能被 cv2 安全使用
        im = im.reshape(bmp_info['bmHeight'], bmp_info['bmWidth'], 4).copy()
        im = im[:, :, :3]                            # 去掉 alpha，保留 BGR

        if setting.get('resolution') != [2560, 1440]:
            im = cv2.resize(im, (2560, 1440), interpolation=cv2.INTER_AREA)
        return im
    except Exception as e:
        log(f'截图异常: {e}')
        return None
    finally:
        # 必须释放 GDI 资源，否则长时间循环运行会句柄泄漏
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
            self._hwnd = get_hwnd(window_title)
            self._frame = None
            self._fail_count = 0
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._loop, name='ScreenshotLoop', daemon=True
            )
            self._thread.start()
            log(f'通用截图服务已启动: {window_title} (间隔 {self._interval}s)')

    def stop(self, timeout=2):
        """停止循环截图。最后一帧会保留，便于调用方继续读取。"""
        with self._lock:
            self._stop_locked(timeout)

    def _stop_locked(self, timeout=2):
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

    def _loop(self):
        stop_event = self._stop_event
        while not stop_event.is_set():
            began = time.time()
            frame = self._grab()
            if frame is not None:
                self._frame = frame        # 原子替换，绝不原地修改
                self._fail_count = 0
            else:
                self._fail_count += 1
                if self._fail_count in (1, 100) or self._fail_count % 500 == 0:
                    log(f'截图失败（第 {self._fail_count} 次），等待窗口 {self._window_title} ...')
                self._hwnd = get_hwnd(self._window_title)   # 窗口可能重启了

            spare = self._interval - (time.time() - began)
            if spare > 0:
                # 用 wait 而不是 sleep，停止时能立即退出，不会卡住 timeout
                stop_event.wait(spare)

    def _grab(self):
        if not self._hwnd or not win32gui.IsWindow(self._hwnd):
            self._hwnd = get_hwnd(self._window_title)
        if not self._hwnd:
            return None
        return capture_hwnd(self._hwnd)


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
