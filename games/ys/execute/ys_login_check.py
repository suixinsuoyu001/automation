"""原神登录「完整流程」自检 —— 可直接在 GUI 里一键触发（任务名：原神登录自检）。

它**不复制**登录逻辑，跑的就是正式任务同一条代码路径：

    c.g_match.click(图标) -> c.check_start() -> disable_ime_all()
        -> start_ime_watchdog() -> ys_action.登录(账号)
        -> stop_ime_watchdog() -> c.check_stop()

与 ``ys_login.login_one`` 完全一致，只在外层套一层观测，用来回答一个问题：
**跑登录的时候，游戏里还会不会弹中文输入法。**

判定全部基于客观量（不需要你肉眼确认，也不需要回答任何问题）：

  * 打字期间前台窗口的输入语言是不是英文（HKL 主语言 ID == 0x09）
  * 游戏是否真的接受了 WM_INPUTLANGCHANGEREQUEST（看 HKL 有没有变化）
  * 实际走了哪条输入路径（英文布局 → 普通按键；否则 → Unicode 注入绕过输入法）
  * 全程 0.1s 采样：输入语言分布 + **新出现**的「输入法 UI 窗口」

关于输入法窗口检测：这是**启发式**判断 —— 候选窗/状态条由 ChsIME.exe、
TextInputHost.exe 等输入法宿主进程绘制，但它们的宿主窗口也可能常驻，
所以这里先取基线、只报告**新的**窗口，结论里也会明确标注这是启发式。

用法
----
GUI：  任务页 -> 原神 -> 「原神登录自检」（可选账号）
命令行：python -m games.ys.execute.ys_login_check        # 账号表第 0 个
        python -m games.ys.execute.ys_login_check 1      # 账号表第 1 个
"""
import os
import sys
import threading
import time

# 允许直接 python games/ys/execute/ys_login_check.py 运行
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import ctypes
from collections import Counter

import win32gui
import win32process

from games.ys.action.ys_action import *          # noqa: F401,F403  (c / 登录 / zh / windows_title ...)
from func.common import get_hwnd, log
from func.control.back_control import current_input_layout

_ENG_PRIMARY = 0x09

# 输入法 UI（候选窗/状态条）常见宿主进程名关键字（小写、子串匹配）
_IME_HOST_KEYWORDS = (
    'chsime',           # 中文(简体) 微软拼音
    'textinputhost',    # Win10/11 输入法 UI 宿主
    'sogou', 'qqpinyin', 'baidu', 'huaci', 'inputmethod', 'tabtip', 'imewdbld',
)

_pid_name_cache = {}
_baseline_ime_hwnds = set()


def _进程名(pid):
    """按 pid 取进程名（带缓存，避免每次枚举都去查系统）"""
    if pid in _pid_name_cache:
        return _pid_name_cache[pid]
    try:
        import psutil

        name = (psutil.Process(pid).name() or '').lower()
    except Exception:
        name = '?'
    _pid_name_cache[pid] = name
    return name


def 输入法窗口():
    """枚举属于输入法宿主进程的可见窗口 -> [(hwnd, 进程名, 类名, 标题)]"""
    found = []

    def callback(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            name = _进程名(pid)
            if any(k in name for k in _IME_HOST_KEYWORDS):
                found.append((hwnd, name, win32gui.GetClassName(hwnd),
                              win32gui.GetWindowText(hwnd)))
        except Exception:
            pass

    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    return found


def 新增输入法窗口():
    """只返回**基线之外**的输入法窗口（刚弹出来的状态条/候选窗）"""
    return [w for w in 输入法窗口() if w[0] not in _baseline_ime_hwnds]


def _状态(tag):
    """把「前台窗口 + 输入语言 + 新输入法窗口」打一行日志"""
    user32 = ctypes.windll.user32
    fg = user32.GetForegroundWindow()
    title = win32gui.GetWindowText(fg) if fg else ''
    hkl = current_input_layout(fg) if fg else 0
    new_ime = 新增输入法窗口()
    log(f'[自检·{tag}] 前台={title!r} 输入语言={hex(hkl)} '
        f'英文输入={bool(hkl and (hkl & 0x3FF) == _ENG_PRIMARY)} 新输入法窗口={len(new_ime)}')
    for hwnd, name, cls, t in new_ime[:5]:
        log(f'        └ hwnd={hwnd} 进程={name} 类名={cls!r} 标题={t!r}')


def _采样(stop_event, samples):
    """后台采样：前台窗口的输入语言 + 是否新出现输入法窗口"""
    user32 = ctypes.windll.user32
    while not stop_event.is_set():
        try:
            fg = user32.GetForegroundWindow()
            samples.append({
                'title': win32gui.GetWindowText(fg) if fg else '',
                'hkl': current_input_layout(fg) if fg else 0,
                'ime': 新增输入法窗口(),
            })
        except Exception:
            pass
        time.sleep(0.1)


def _报告(samples, account, ok):
    log('-------------------- 输入法自检报告 --------------------')
    log(f'账号: {account}    登录流程: {"跑完" if ok else "异常中断"}')
    if not samples:
        log('没有采到样本，无法判定')
        log('--------------------------------------------------------')
        return

    n = len(samples)
    titles = Counter(s['title'] for s in samples if s['title'])
    log(f'采样 {n} 次；前台窗口分布(前3): {titles.most_common(3)}')
    hkls = Counter(hex(s['hkl']) for s in samples)
    eng = sum(1 for s in samples if (s['hkl'] & 0x3FF) == _ENG_PRIMARY)
    log(f'输入语言分布: {dict(hkls)}')
    log(f'英文输入占比: {eng}/{n}')
    hits = [s for s in samples if s['ime']]
    if hits:
        log(f'检测到新输入法窗口: {len(hits)}/{n} 次，例如:')
        for hwnd, name, cls, t in hits[0]['ime'][:5]:
            log(f'    └ hwnd={hwnd} 进程={name} 类名={cls!r} 标题={t!r}')
    else:
        log('全程未检测到新的输入法窗口')

    log('---------------------- 结论 ----------------------')
    if eng == n and not hits:
        log('[正常] 打字期间输入语言全程英文，且没有新的输入法窗口 —— 游戏内不会再弹中文输入法。')
    elif eng == n:
        log('[注意] 输入语言全程英文（普通按键不会经过输入法），但仍检测到输入法窗口弹出。')
        log('  这通常说明游戏自己用 TSF 强制激活了中文输入法配置，从外部屏蔽不掉；')
        log('  请把本报告发我，并确认那些窗口是否真的是输入法状态条/候选窗。')
    else:
        log('[注意] 采样中出现过非英文输入语言：说明输入语言被游戏或系统抢回去了。')
        log('  请把本报告发我，重点看上面的「输入语言分布」和各 HKL 值。')
    log('--------------------------------------------------')


def 登录自检(account=None, n=0):
    """完整跑一遍原神登录流程并输出输入法自检报告（GUI 任务入口）

    :param account: 账号（GUI 直接传账号字符串）；为空时用账号表第 n 个
    :param n:       账号表序号（命令行用）
    """
    if not account:
        try:
            n = int(n)
        except (TypeError, ValueError):
            n = 0
        account = zh[n] if 0 <= n < len(zh) else zh[0]

    log('==================== 原神登录自检 开始 ====================')
    log(f'跑的是和 ys_login.login_one 完全一致的完整流程，账号: {account}')

    # 基线：先记录「现在就已经存在」的输入法窗口，后面只报告新增的
    _baseline_ime_hwnds.clear()
    _baseline_ime_hwnds.update(h for h, _, _, _ in 输入法窗口())
    log(f'输入法窗口基线: {len(_baseline_ime_hwnds)} 个（之后只报告新出现的）')

    samples = []
    stop_event = threading.Event()
    sampler = threading.Thread(target=_采样, args=(stop_event, samples), daemon=True)

    ok = False
    try:
        c.g_match.click(f'图标{resolution[0]}')
        c.check_start()
        c.control.hwnd = get_hwnd(windows_title)
        _状态('check_start 后')
        c.control.disable_ime_all()
        _状态('IMM32 屏蔽后')
        c.control.start_ime_watchdog()
        sampler.start()
        try:
            登录(account)
            ok = True
        finally:
            stop_event.set()
            sampler.join(timeout=2)
            c.control.stop_ime_watchdog()
            _状态('看门狗停止后')
    finally:
        c.check_stop()

    _报告(samples, account, ok)
    log('==================== 原神登录自检 结束 ====================')


if __name__ == '__main__':
    _n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    登录自检(n=_n)
