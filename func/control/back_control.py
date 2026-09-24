import atexit
import time,win32gui,win32con,win32api,threading
from func.common import *
from pynput.mouse import Controller


key_code = {
    'esc':win32con.VK_ESCAPE,
    'enter':win32con.VK_RETURN,
    'space':win32con.VK_SPACE,
    'shift':win32con.VK_LSHIFT,
    'f1':win32con.VK_F1,
    'f2':win32con.VK_F2,
    'f3':win32con.VK_F3,
    'f4':win32con.VK_F4,
    'alt': 18
}

# 常量和结构体定义
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong),
                ("u", _INPUT_UNION)]


# ---- 键盘注入用结构（SendInput 直接注入 Unicode 字符，绕过中文输入法）----
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _INPUT_UNION_FULL(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT)]


class INPUT_FULL(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong),
                ("u", _INPUT_UNION_FULL)]


def write_text(text, delay=0.01):
    """用 SendInput + KEYEVENTF_UNICODE 逐字符注入，**绕过键盘布局与输入法**。

    普通模拟按键(keyboard.write/pyautogui)会先经过输入法翻译，中文输入法激活时
    会把账号里的字母组词成中文；而 KEYEVENTF_UNICODE 由系统直接生成 WM_CHAR，
    不经过输入法，因此账号密码不会被录成中文。

    :return: 实际注入成功的字符数（0 表示 SendInput 被拦截，调用方应回退到 keyboard.write）
    """
    user32 = ctypes.windll.user32
    extra = ctypes.c_ulong(0)
    ptr = ctypes.pointer(extra)
    sent = 0
    for ch in text:
        code = ord(ch)
        down = INPUT_FULL(type=1, u=_INPUT_UNION_FULL(
            ki=KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, ptr)))
        up = INPUT_FULL(type=1, u=_INPUT_UNION_FULL(
            ki=KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ptr)))
        if user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(down)) == 1:
            sent += 1
        user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(up))
        time.sleep(delay)
    return sent


def move_mouse_relative(dx, dy):
    extra = ctypes.c_ulong(0)
    mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    inp = INPUT(type=INPUT_MOUSE, u=_INPUT_UNION(mi=mi))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def smooth_move(to_x, to_y, steps=30, delay=0.01):
    # 获取当前鼠标位置
    from_x, from_y = win32api.GetCursorPos()
    dx = (to_x - from_x) / steps
    dy = (to_y - from_y) / steps

    for i in range(steps):
        move_mouse_relative(int(dx), int(dy))
        time.sleep(delay)

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# ==================== 输入法(IME)屏蔽相关 ====================
# 通过 IMM32 API 解除窗口与输入法的关联，从而在游戏内屏蔽中文输入法
imm32 = ctypes.WinDLL('imm32')

# 保存被解除关联的窗口原始输入法上下文，便于恢复
_ime_contexts = {}


def disable_ime(hwnd):
    """屏蔽指定窗口的输入法（解除窗口与输入法上下文的关联）

    :param hwnd: 窗口句柄
    :return: 成功返回 True
    """
    if not hwnd:
        return False
    try:
        # 获取当前输入法上下文并保存
        h_ime = imm32.ImmGetContext(hwnd)
        if h_ime:
            _ime_contexts[hwnd] = h_ime
            imm32.ImmReleaseContext(hwnd, h_ime)
        # 将窗口的输入法上下文设为 NULL，屏蔽输入法
        imm32.ImmAssociateContext(hwnd, None)
        log(f'已屏蔽窗口输入法 hwnd={hwnd}')
        return True
    except Exception as e:
        log(f'屏蔽输入法失败: {e}')
        return False


def enable_ime(hwnd):
    """恢复指定窗口的输入法

    :param hwnd: 窗口句柄
    :return: 成功返回 True
    """
    if not hwnd:
        return False
    try:
        h_ime = _ime_contexts.pop(hwnd, None)
        if h_ime:
            imm32.ImmAssociateContext(hwnd, h_ime)
        else:
            # 没有保存过则创建一个默认上下文
            h_ime = imm32.ImmCreateContext()
            imm32.ImmAssociateContext(hwnd, h_ime)
        log(f'已恢复窗口输入法 hwnd={hwnd}')
        return True
    except Exception as e:
        log(f'恢复输入法失败: {e}')
        return False


def set_ime_english(hwnd):
    """将指定窗口的输入法强制切换为英文模式（半角/英文标点）

    :param hwnd: 窗口句柄
    :return: 成功返回 True
    """
    if not hwnd:
        return False
    try:
        h_ime = imm32.ImmGetContext(hwnd)
        if not h_ime:
            return False
        # IME_CMODE_ALPHANUMERIC = 0x0000 英文数字模式
        # IME_SMODE_NONE = 0x0000
        imm32.ImmSetConversionStatus(h_ime, 0x0000, 0x0000)
        imm32.ImmReleaseContext(hwnd, h_ime)
        log(f'已切换窗口输入法为英文 hwnd={hwnd}')
        return True
    except Exception as e:
        log(f'切换输入法为英文失败: {e}')
        return False


def _enum_child_windows(hwnd):
    """枚举指定窗口的所有子窗口句柄"""
    children = []
    try:
        win32gui.EnumChildWindows(hwnd, lambda h, _: children.append(h), None)
    except Exception:
        pass
    return children


def disable_ime_all(hwnd):
    """屏蔽指定窗口及其所有子窗口的输入法

    游戏窗口的输入焦点往往在子窗口上，只处理主窗口无效，
    因此需要递归处理所有子窗口。

    :param hwnd: 主窗口句柄
    :return: 成功处理的窗口数量
    """
    if not hwnd:
        return 0
    count = 0
    targets = [hwnd] + _enum_child_windows(hwnd)
    for h in targets:
        try:
            h_ime = imm32.ImmGetContext(h)
            if h_ime:
                _ime_contexts[h] = h_ime
                imm32.ImmReleaseContext(h, h_ime)
            imm32.ImmAssociateContext(h, None)
            count += 1
        except Exception:
            pass
    log(f'已屏蔽窗口及子窗口输入法，共 {count} 个窗口')
    return count


def close_ime(hwnd):
    """关闭指定窗口的输入法打开状态（关闭中文输入状态）

    :param hwnd: 窗口句柄
    :return: 成功返回 True
    """
    if not hwnd:
        return False
    try:
        h_ime = imm32.ImmGetContext(hwnd)
        if not h_ime:
            return False
        # 关闭输入法（IME_CMODE 关闭，即英文输入状态）
        imm32.ImmSetOpenStatus(h_ime, False)
        imm32.ImmReleaseContext(hwnd, h_ime)
        return True
    except Exception as e:
        log(f'关闭输入法失败: {e}')
        return False


def switch_to_english_layout():
    """把当前线程的输入法切换为英文键盘布局（**会改动系统输入语言，慎用**）

    注意：这个函数改的是「系统输入语言」，在「所有应用共用一种输入法」的机器上
    等于整机变英文。登录流程已经不使用它了 —— 请改用
    set_window_input_english()：临时切、用完立刻还原。

    :return: 成功返回 True
    """
    try:
        user32 = ctypes.windll.user32
        # 获取当前前台窗口
        hwnd = user32.GetForegroundWindow()
        # 获取当前线程的键盘布局
        cur_layout = user32.GetKeyboardLayout(0)
        # 英文布局句柄（flag=0，只加载不 KLF_ACTIVATE，避免顺带激活到本进程）
        en_layout = _find_english_layout()
        if en_layout and cur_layout != en_layout:
            # 请求切换输入语言
            WM_INPUTLANGCHANGEREQUEST = 0x0050
            user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, en_layout)
            # 同时直接激活（对当前线程生效）
            user32.ActivateKeyboardLayout(en_layout, 0)
            log('已切换系统输入法为英文布局')
            return True
        return False
    except Exception as e:
        log(f'切换系统输入法失败: {e}')
        return False


def _window_pid(hwnd):
    """取窗口所属进程 id（失败返回 None）"""
    try:
        return win32process.GetWindowThreadProcessId(hwnd)[1]
    except Exception:
        return None


def _iter_window_tree(hwnd):
    """返回 hwnd 自身 + 其根窗口 + 它们的所有子窗口

    原神登录界面的输入框在 CEF/webview 子窗口里，单独处理主窗口是不够的。
    """
    if not hwnd:
        return []
    user32 = ctypes.windll.user32
    targets = [hwnd]
    try:
        root = user32.GetAncestor(hwnd, 2)  # GA_ROOT
        if root and root not in targets:
            targets.append(root)
    except Exception:
        pass
    for h in list(targets):
        for child in _enum_child_windows(h):
            if child not in targets:
                targets.append(child)
    return targets


def _block_ime_on(hwnd):
    """解除单个窗口与输入法的关联，并关闭它的中文输入状态"""
    try:
        h_ime = imm32.ImmGetContext(hwnd)
        if h_ime:
            # setdefault：保留第一次拿到的原始上下文，便于 enable_ime 恢复
            _ime_contexts.setdefault(hwnd, h_ime)
            imm32.ImmSetOpenStatus(h_ime, False)
            imm32.ImmSetConversionStatus(h_ime, 0x0000, 0x0000)  # 英文数字 + 半角
            imm32.ImmReleaseContext(hwnd, h_ime)
        imm32.ImmAssociateContext(hwnd, None)
        return True
    except Exception:
        return False


def force_english_input(hwnd=None):
    """屏蔽「马上要接收键盘输入的那个窗口」的中文输入法（打账号/密码前调用）

    **只操作目标窗口自己的输入法关联（window-local），绝不修改系统输入语言/键盘布局**：
    Windows 的 `WM_INPUTLANGCHANGEREQUEST` / `ActivateKeyboardLayout` 是按应用(甚至整机)
    记住输入语言的，一改就会导致「跑完脚本游戏外也没法打中文」。
    这里只用 ImmAssociateContext(h, NULL)，它只影响这一个窗口。

    原神这类 CEF/webview 登录界面会在输入框获得焦点时把输入法重新挂上，
    所以除了目标窗口，还会处理它的根窗口、所有子窗口，
    以及「与目标窗口同进程的前台顶层窗口」（原神登录界面可能是独立的 webview 顶层窗口）。

    :param hwnd: 游戏主窗口句柄；None 时只处理当前前台窗口
    :return: 是否至少处理了一个窗口
    """
    user32 = ctypes.windll.user32
    fg = user32.GetForegroundWindow()

    targets = []
    # 前台窗口若属于游戏进程，它才是真正接收键盘输入的窗口
    if hwnd and fg and _window_pid(fg) == _window_pid(hwnd):
        targets.append(fg)
    if hwnd:
        targets.append(hwnd)
    if not targets and fg:
        targets.append(fg)
    if not targets:
        return False

    ok = False
    for t in targets:
        for h in _iter_window_tree(t):
            if _block_ime_on(h):
                ok = True
    log(f'已屏蔽窗口输入法 hwnd={targets[0]}')
    return ok


def enable_ime_all(hwnd):
    """把被 force_english_input / disable_ime_all 屏蔽掉的窗口输入法还回去

    只恢复此前**确实保存过**输入法上下文的窗口（不做 ImmCreateContext），
    所以不会给本来就没有输入法的窗口凭空装上输入法。
    """
    if not hwnd:
        return 0
    count = 0
    for h in _iter_window_tree(hwnd):
        h_ime = _ime_contexts.pop(h, None)
        if not h_ime:
            continue
        try:
            imm32.ImmAssociateContext(h, h_ime)
            count += 1
        except Exception:
            pass
    log(f'已恢复 {count} 个窗口的输入法')
    return count


# ---- 输入语言的「临时」切换（针对不受 IMM32 控制的输入法，如微软拼音 TSF）----
# 原神这类游戏的窗口没有 IMM32 输入法上下文（ImmGetContext 返回 0），
# 而微软拼音是 TSF 服务，ImmAssociateContext 对它无效。
# 这种情况下唯一能在游戏内屏蔽中文输入的办法，就是把**该窗口线程的输入语言**临时切成英文；
# 用完必须还原，否则会变成「跑完脚本整机/该应用一直停在英文」。
_ENG_PRIMARY = 0x09      # 英语的主语言 ID（LANGID 低 10 位）
_ZH_PRIMARY = 0x04       # 中文的主语言 ID
_saved_hkl = {}          # 窗口 -> 切走之前的输入语言
_layout_log_state = {}   # 窗口 -> 上次打印过的 (原, 现)，避免看门狗刷屏

# 总开关：是否允许「把输入语言临时切成英文」这套屏蔽手段。
# 如果你的系统是「所有应用共用一种输入法」，切换会波及整个桌面；
# 万一出现「跑完脚本键盘留在英文」，把它改成 False 就能彻底关掉这套机制
# （关掉后仍保留 IMM32 屏蔽 + Unicode 注入兜底，只是可能还会弹输入法状态条）。
ENABLE_INPUT_LANGUAGE_SWITCH = True


def _safe_log(*args):
    """退出阶段 stdout 可能已关闭，日志失败绝不能影响还原动作"""
    try:
        log(*args)
    except Exception:
        pass


def _window_layout(hwnd):
    """取窗口所属线程当前的输入语言(HKL)，0 表示取不到"""
    user32 = ctypes.windll.user32
    try:
        tid = user32.GetWindowThreadProcessId(hwnd, None)
        hkl = user32.GetKeyboardLayout(tid) if tid else user32.GetKeyboardLayout(0)
        return hkl & 0xFFFFFFFF
    except Exception:
        return 0


def input_is_english(hwnd=None):
    """当前前台窗口（或指定窗口）的输入语言是不是英文

    是英文时，普通模拟按键不会经过输入法组词，也就不需要 KEYEVENTF_UNICODE 注入；
    而 Unicode 注入(VK_PACKET)虽然字符正确，但部分输入法会因此弹出状态条/候选窗。
    """
    user32 = ctypes.windll.user32
    target = hwnd or user32.GetForegroundWindow()
    if not target:
        return False
    return (_window_layout(target) & 0x3FF) == _ENG_PRIMARY


def current_input_layout(hwnd=None):
    """取当前（或指定窗口）的输入语言 HKL 数值 —— 供日志/自检使用"""
    user32 = ctypes.windll.user32
    target = hwnd if hwnd is not None else user32.GetForegroundWindow()
    return _window_layout(target) if target else 0


def _find_layout_by_primary(primary):
    """在系统**已安装**的输入语言里找主语言 ID == primary 的布局（0x04=中文, 0x09=英文）

    优先复用系统里已经装好的布局，避免再往用户的输入法列表里加新的键盘布局。
    """
    user32 = ctypes.windll.user32
    try:
        count = user32.GetKeyboardLayoutList(0, None)
        if count:
            buf = (ctypes.c_void_p * count)()
            user32.GetKeyboardLayoutList(count, buf)
            for item in buf:
                hkl = int(item) if item else 0
                if hkl and (hkl & 0x3FF) == primary:
                    return hkl & 0xFFFFFFFF
    except Exception:
        pass
    return 0


def _find_english_layout():
    """英文布局：优先用系统已装好的；没有才加载美式键盘(US)"""
    hkl = _find_layout_by_primary(_ENG_PRIMARY)
    if hkl:
        return hkl
    try:
        # flag=0：只加载，**不要** KLF_ACTIVATE，否则会顺带激活到本进程
        return ctypes.windll.user32.LoadKeyboardLayoutW('00000409', 0) & 0xFFFFFFFF
    except Exception:
        return 0


def _post_layout_change(hwnd, hkl):
    """请求把窗口所属线程的输入语言换成 hkl（由游戏线程自己处理，最稳）"""
    user32 = ctypes.windll.user32
    try:
        user32.PostMessageW(hwnd, 0x0050, 0, hkl)      # WM_INPUTLANGCHANGEREQUEST
    except Exception:
        pass
    try:
        res = ctypes.c_size_t(0)
        user32.SendMessageTimeoutW(hwnd, 0x0050, 0, hkl, 0x0002, 200, ctypes.byref(res))
    except Exception:
        pass


def set_window_input_english(hwnd=None):
    """把目标窗口（默认当前前台窗口）的输入语言**临时**切成英文，并记住原来的

    只在「游戏处于前台」时调用；必须用 restore_window_input() 还原。
    :return: 是否已处于/已切到英文
    """
    if not ENABLE_INPUT_LANGUAGE_SWITCH:
        return False
    user32 = ctypes.windll.user32
    target = hwnd or user32.GetForegroundWindow()
    if not target:
        return False
    try:
        if not user32.IsWindow(target):
            return False
    except Exception:
        return False
    cur = _window_layout(target)
    if cur and (cur & 0x3FF) == _ENG_PRIMARY:
        return True                      # 已经是英文输入，不用动
    en = _find_english_layout()
    if not en:
        return False
    # setdefault：每个窗口只记第一次，避免把中途的英文当成「原始值」存下来
    _saved_hkl.setdefault(target, cur)
    _post_layout_change(target, en)
    # 读回真实结果：日志里「现=」才是游戏是否真的接受切换的证据。
    # 若 现 和 原 一样，说明这个游戏忽略了 WM_INPUTLANGCHANGEREQUEST。
    time.sleep(0.05)
    now = _window_layout(target)
    state = (cur, now)
    if _layout_log_state.get(target) != state:
        _layout_log_state[target] = state
        log(f'已临时切英文输入 hwnd={target}（原={hex(cur)} 现={hex(now)}）')
    return True


def restore_window_input(hwnd=None, retries=3, wait=0.2):
    """把之前临时切走的输入语言还回去（会**读回验证**，没还成功就重试）

    关键点：**只有确认已经回到原来的输入语言，才丢掉记录**。
    否则后面的 atexit / ``python tool/ime_diagnose.py --chinese`` 还能再试一次，
    不会出现「投递被忽略 -> 记录被丢掉 -> 键盘永久留在英文」。
    """
    user32 = ctypes.windll.user32
    targets = [hwnd] if hwnd else list(_saved_hkl.keys())
    done = 0
    for t in targets:
        hkl = _saved_hkl.get(t)
        if not hkl:
            _saved_hkl.pop(t, None)
            continue
        try:
            if not user32.IsWindow(t):
                # 目标窗口已销毁，它所在线程也没了，输入语言不会残留 -> 丢掉记录
                _saved_hkl.pop(t, None)
                continue
        except Exception:
            continue

        for _ in range(max(1, int(retries))):
            _post_layout_change(t, hkl)
            time.sleep(wait)
            if _window_layout(t) == hkl:
                _saved_hkl.pop(t, None)
                done += 1
                _safe_log(f'已还原输入语言 hwnd={t} -> {hex(hkl)}')
                break
        else:
            # 还原失败：保留记录，交给 atexit / ime_diagnose --chinese 再试
            _safe_log(f'[注意] 输入语言还原失败 hwnd={t}：期望 {hex(hkl)}，'
                      f'当前 {hex(_window_layout(t))}；'
                      f'可按 Win+空格 手动切回，或运行 python tool/ime_diagnose.py --chinese')
    return done


def force_chinese_input(hwnd=None):
    """兜底恢复：把窗口输入语言切回中文（万一被留在英文时用）

    :return: 成功返回 True
    """
    user32 = ctypes.windll.user32
    target = hwnd or user32.GetForegroundWindow()
    if not target:
        return False
    zh = _find_layout_by_primary(_ZH_PRIMARY)
    if not zh:
        _safe_log('系统里找不到中文输入语言，无法自动切回，请按 Win+空格 手动切换')
        return False
    _saved_hkl.pop(target, None)     # 手动恢复后原来那条记录就作废了
    for _ in range(3):
        _post_layout_change(target, zh)
        time.sleep(0.2)
        if _window_layout(target) == zh:
            _safe_log(f'已把输入语言切回中文 hwnd={target} -> {hex(zh)}')
            return True
    _safe_log(f'[注意] 切回中文失败，当前 {hex(_window_layout(target))}，请按 Win+空格 手动切换')
    return False


def _restore_all_on_exit():
    """进程退出兜底：绝不把用户的输入语言留在英文"""
    try:
        restore_window_input()
    except Exception:
        pass


# ==================== 输入法看门狗（持续屏蔽窗口输入法） ====================
_ime_watchdog_thread = None
_ime_watchdog_stop = None
# 记录看门狗作用的窗口句柄，停止时把输入法还给游戏
_ime_watchdog_hwnd = None


def _is_game_foreground(hwnd):
    """判断前台窗口是否属于游戏

    覆盖三种情况：
      * 前台就是游戏主窗口；
      * 前台是游戏主窗口的子窗口（子窗口的根窗口等于游戏窗口）；
      * 前台是**同进程的其它顶层窗口** —— 原神的登录界面是独立的 CEF/webview
        窗口，不在游戏主窗口的子窗口树里，只靠父子关系判断会漏掉。
    """
    if not hwnd:
        return False
    try:
        user32 = ctypes.windll.user32
        fg = user32.GetForegroundWindow()
        if not fg:
            return False
        if fg == hwnd:
            return True
        # 前台窗口可能是游戏的子窗口，向上查找根窗口
        if user32.GetAncestor(fg, 2) == hwnd:   # GA_ROOT = 2
            return True
        # 同一进程的其它顶层窗口（如 CEF 登录界面）
        return _window_pid(fg) == _window_pid(hwnd)
    except Exception:
        return False


def _ime_watchdog_loop(hwnd, interval):
    """后台循环：仅在游戏窗口处于前台时，持续屏蔽它的输入法

    两层手段：
      1. 窗口级：持续解除窗口与输入法上下文的关联（对 IMM32 类输入法有效）；
      2. 输入语言级：把游戏线程的输入语言**临时**切成英文 —— 对微软拼音这类
         TSF 输入法，这是唯一能真正屏蔽中文输入的办法。
    游戏一旦不在前台（或看门狗停止），立刻把输入语言还原，
    所以游戏外其它程序输入中文完全不受影响。
    """
    user32 = ctypes.windll.user32
    tick = 0
    while not _ime_watchdog_stop.is_set():
        try:
            # 仅在游戏窗口处于前台时才干预输入法
            if _is_game_foreground(hwnd):
                fg = user32.GetForegroundWindow()
                if fg:
                    # 原神等 CEF 登录界面在输入框获得焦点时会自己把输入法挂回来，
                    # 所以每约 1 秒把整棵窗口树重新解除一次关联，其余时刻只处理前台窗口
                    if tick % 5 == 0:
                        for h in _iter_window_tree(fg):
                            _block_ime_on(h)
                    else:
                        _block_ime_on(fg)
                    # 原神窗口没有 IMM32 上下文、微软拼音又是 TSF 服务，
                    # 只能把该窗口线程的输入语言临时切成英文来屏蔽中文输入
                    set_window_input_english(fg)
            else:
                # 游戏不在前台：立刻把输入语言还给用户，保证游戏外正常打中文
                restore_window_input()
        except Exception:
            pass
        tick += 1
        time.sleep(interval)



def start_ime_watchdog(hwnd=None, interval=0.2):
    """启动输入法看门狗线程，持续屏蔽游戏窗口的输入法

    游戏在前台时：持续解除窗口输入法关联 + 把输入语言临时切英文；
    游戏失焦 / 看门狗停止 / 进程退出时：一律还原输入语言，保证游戏外正常打中文。

    :param hwnd: 游戏主窗口句柄（可选）
    :param interval: 检测间隔（秒）
    """
    global _ime_watchdog_thread, _ime_watchdog_stop, _ime_watchdog_hwnd
    if _ime_watchdog_thread and _ime_watchdog_thread.is_alive():
        return
    _ime_watchdog_hwnd = hwnd
    _ime_watchdog_stop = threading.Event()
    _ime_watchdog_thread = threading.Thread(
        target=_ime_watchdog_loop, args=(hwnd, interval), daemon=True
    )
    _ime_watchdog_thread.start()
    atexit.register(_restore_all_on_exit)   # 兜底：进程退出时一定还原输入语言
    log('输入法看门狗已启动')


def stop_ime_watchdog():
    """停止输入法看门狗线程，并把被屏蔽的窗口输入法还给游戏"""
    global _ime_watchdog_thread, _ime_watchdog_stop, _ime_watchdog_hwnd
    if _ime_watchdog_stop:
        _ime_watchdog_stop.set()
    # 先还原一次：看门狗线程可能正好卡在 sleep 里，早一点把还原请求发出去
    restore_window_input()
    if _ime_watchdog_thread:
        _ime_watchdog_thread.join(timeout=2)
    _ime_watchdog_thread = None
    _ime_watchdog_stop = None
    # 任务结束后恢复：游戏内打字（聊天）也能正常用中文
    if _ime_watchdog_hwnd:
        enable_ime_all(_ime_watchdog_hwnd)
        _ime_watchdog_hwnd = None
    # 线程确实停了以后再还原一次，确保最终状态一定不是英文
    restore_window_input()
    _safe_log('输入法看门狗已停止')


class Control():




    def __init__(self,hwnd = None):
        self.hwnd = hwnd
    def get_key_code(self,key):
        if type(key) == str and len(key) == 1:
            return ord(key.upper())
        elif key_code.get(key):
            return key_code.get(key)
        else:
            return key

    def send_key_down(self,key):
        # mouse = Controller()
        # last_position = mouse.position  # 记录鼠标初始位置
        # ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYDOWN, self.get_key_code(key), 0)
        # time.sleep(0.01)
        # mouse.position = last_position
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYDOWN, self.get_key_code(key), 0)

    def send_key_up(self,key):
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYUP, self.get_key_code(key), 0)


    def send_key(self,key,t = 0.1):
        self.send_key_down(key)
        time.sleep(t)
        self.send_key_up(key)

    def get_mouse_position(self):
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def set_mouse_position(self,x, y):
        ctypes.windll.user32.SetCursorPos(x, y)

    def activate(self):
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_ACTIVATE, 1, 0)

    def inactivate(self):
        # 解除输入焦点绑定
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_INACTIVE, 0)


    def click(self,point):
        x, y = point  # 点击的坐标（相对于窗口客户区）
        ctypes.windll.user32.SetCursorPos(x, y)

        l_param = (y << 16) | x  # 计算坐标参数
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        time.sleep(0.05)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONUP, 0, l_param)

    def click_mid(self):
        x, y = 0, 0  # 目标坐标
        lParam = (y << 16) | x
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, lParam)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MBUTTONUP, 0, lParam)

    def click_right(self):
        x, y = 0, 0  # 目标坐标
        lParam = (y << 16) | x
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        time.sleep(0.5)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
    def scroll(self, count, point):
        count = int(count)
        x, y = point  # 点击的坐标（相对于窗口客户区）
        lParam = (y << 16) | (x & 0xFFFF)  # 手动构造 lParam
        wParam = (win32con.WHEEL_DELTA * count) << 16  # 高16位存滚轮增量，低16位为0
        n = 20
        for i in range(n):
            ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
            time.sleep(0.001)


    def scroll2(self, count, point):
        count = int(count)
        x, y = point  # 点击的坐标（相对于窗口客户区）
        lParam = (y << 16) | (x & 0xFFFF)  # 手动构造 lParam
        wParam = (win32con.WHEEL_DELTA * count) << 16  # 高16位存滚轮增量，低16位为0
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)


    def move_scroll(self,point,delta):
        x, y = point  # 点击的坐标（相对于窗口客户区）
        ctypes.windll.user32.SetCursorPos(x, y)
        l_param = (y << 16) | x  # 计算坐标参数
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        time.sleep(0.01)
        smooth_move(x, y - delta, steps=20, delay=0.001)

        time.sleep(0.3)

    def block_user_input(self):
        ctypes.windll.user32.BlockInput(True)

    def unblock_user_input(self):
        ctypes.windll.user32.BlockInput(False)

    def disable_ime(self):
        """屏蔽当前窗口的输入法（防止游戏内切换成中文输入法）"""
        return disable_ime(self.hwnd)

    def enable_ime(self):
        """恢复当前窗口的输入法"""
        return enable_ime(self.hwnd)

    def set_ime_english(self):
        """将当前窗口输入法切换为英文模式"""
        return set_ime_english(self.hwnd)

    def disable_ime_all(self):
        """屏蔽当前窗口及其所有子窗口的输入法"""
        return disable_ime_all(self.hwnd)

    def close_ime(self):
        """关闭当前窗口的输入法打开状态"""
        return close_ime(self.hwnd)

    def switch_to_english_layout(self):
        """将系统输入法切换为英文键盘布局"""
        return switch_to_english_layout()

    def start_ime_watchdog(self, interval=0.2):
        """启动输入法看门狗，持续强制英文输入"""
        return start_ime_watchdog(self.hwnd, interval)

    def stop_ime_watchdog(self):
        """停止输入法看门狗"""
        return stop_ime_watchdog()

    def force_english_input(self):
        """屏蔽「即将接收键盘输入的窗口」的中文输入法（只动窗口，不改系统输入语言）"""
        return force_english_input(self.hwnd)

    def enable_ime_all(self):
        """把被屏蔽的窗口输入法还给游戏（任务结束后调用，游戏内即可正常打中文）"""
        return enable_ime_all(self.hwnd)

    def set_input_english(self):
        """把输入语言临时切成英文（针对微软拼音这类不受 IMM32 控制的输入法）"""
        return set_window_input_english(self.hwnd)

    def restore_input(self):
        """还原被临时切走的输入语言（打完字/任务结束必须调用）"""
        return restore_window_input()

    def force_chinese_input(self):
        """兜底：把输入语言切回中文（键盘被留在英文时用）"""
        return force_chinese_input(None)

    def input_is_english(self):
        """当前输入语言是否已是英文（是则普通按键输入不会碰到输入法）"""
        return input_is_english(self.hwnd)

    def current_input_layout(self):
        """当前输入语言的 HKL 数值（日志/自检用）"""
        return current_input_layout(self.hwnd)

    def write_text(self, text, delay=0.01):
        """注入文本（SendInput + KEYEVENTF_UNICODE，绕过输入法），返回成功字符数"""
        return write_text(text, delay)




    def move(self):
        x, y = 500, 300  # 目标坐标
        # lParam = 低16位为x坐标，高16位为y坐标
        lParam = (y << 16) | x
        # 发送 WM_MOUSEMOVE 消息
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)

    def send_left_shift(slef,hwnd):
        VK_LSHIFT = 0xA0
        scan_code = ctypes.windll.user32.MapVirtualKeyW(VK_LSHIFT, 0)

        # 构造 lParam
        lparam_down = 1 | (scan_code << 16)  # 按下
        lparam_up = (1 << 31) | (1 << 30) | (scan_code << 16)  # 抬起

        # 按下 Shift
        ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYDOWN, VK_LSHIFT, lparam_down)
        time.sleep(0.05)
        # 抬起 Shift
        ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYUP, VK_LSHIFT, lparam_up)

    def click_input(self,point,text):
        x, y = point  # 点击的坐标（相对于窗口客户区）
        ctypes.windll.user32.SetCursorPos(x, y)
        l_param = (y << 16) | x  # 计算坐标参数
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        time.sleep(0.05)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONUP, 0, l_param)
        time.sleep(0.02)
        for char in text:
            ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(0.01)

    def test(self,key):
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYUP, key, 0)


if __name__ == '__main__':
    c = Control()
    c.activate()
    c.click_mid()
    # c.move()

    # c.activate()
    # time.sleep(0.2)
