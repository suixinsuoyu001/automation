"""输入法(IME)诊断脚本 —— 在游戏停在「登录其他账号 / 输入账号」界面时运行。

用来确认三件事（这些是「屏蔽中文输入」能否生效的关键）：

  1. 游戏主窗口句柄、类名、进程号，以及它是否还有**独立的 webview 顶层窗口**
     （原神登录界面是 CEF/webview，可能不在主窗口的子窗口树里）；
  2. 每个窗口是否挂着输入法上下文（ImmGetContext 是否非 0）、该窗口线程的键盘布局；
  3. 调用 force_english_input() 之后再复查一遍，判断屏蔽有没有真的生效。

用法：
    python tool/ime_diagnose.py              # 只看现状
    python tool/ime_diagnose.py --force      # 屏蔽一次窗口输入法并复查
    python tool/ime_diagnose.py --restore    # 把窗口输入法还回去
    python tool/ime_diagnose.py --chinese    # 强制把输入语言切回中文（键盘留在英文时用）

判断标准：
    --force 之后「输入法上下文」应变为 无，而「布局」应**保持不变**
    （本方案只动窗口自己的输入法关联，不改系统输入语言，
      所以游戏外其它程序输入中文不会受影响）。
"""
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ctypes

import win32gui
import win32process

from func.common import get_hwnd
from func.control.back_control import (
    _iter_window_tree,
    _window_pid,
    enable_ime_all,
    force_chinese_input,
    force_english_input,
    imm32,
)

TITLES = ['原神', '崩坏：星穹铁道', '鸣潮']


def enum_pid_windows(pid):
    """枚举某个进程的所有可见顶层窗口（CEF 登录界面常常单独一个顶层窗口）"""
    result = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        try:
            if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
                result.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(callback, None)
    return result


def dump_window(hwnd, indent='  '):
    try:
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
    except Exception:
        title = cls = '<?>'
    try:
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
    except Exception:
        tid = pid = '?'
    ctx = 0
    try:
        ctx = imm32.ImmGetContext(hwnd)
        if ctx:
            imm32.ImmReleaseContext(hwnd, ctx)
    except Exception:
        pass
    try:
        layout = ctypes.windll.user32.GetKeyboardLayout(tid)
    except Exception:
        layout = 0
    print(f'{indent}hwnd={hwnd} pid={pid} tid={tid} class={cls!r} '
          f'输入法上下文={"有" if ctx else "无"} 布局={hex(layout & 0xffffffff)} '
          f'标题={title!r}')


def main():
    force = '--force' in sys.argv
    restore = '--restore' in sys.argv
    chinese = '--chinese' in sys.argv

    for title in TITLES:
        hwnd = get_hwnd(title)
        print(f'== 游戏「{title}」: 主窗口 hwnd={hwnd}')
        if not hwnd:
            continue
        pid = _window_pid(hwnd)
        print(f'   进程号={pid}')
        print('   主窗口 + 根窗口 + 所有子窗口：')
        for h in _iter_window_tree(hwnd):
            dump_window(h, '     ')
        print('   同进程的其它可见顶层窗口（webview 等）：')
        for h in enum_pid_windows(pid):
            dump_window(h, '     ')

    user32 = ctypes.windll.user32
    fg = user32.GetForegroundWindow()
    print('== 当前前台窗口：')
    dump_window(fg, '  ')
    print(f'   根窗口={user32.GetAncestor(fg, 2)}')

    if force:
        print('== 执行 force_english_input()（只屏蔽窗口输入法，不改系统输入语言）...')
        print('   结果:', force_english_input())
        time.sleep(0.3)
        print('== 复查前台窗口：')
        dump_window(user32.GetForegroundWindow(), '  ')
        print('   注意：此时「输入法上下文」应变成 无（=该窗口用不了中文输入法），')
        print('         而「布局」应当**保持不变** —— 系统语言没被改动，游戏外中文照常。')

    if restore:
        print('== 执行 enable_ime_all() 恢复窗口输入法 ...')
        print('   结果:', enable_ime_all(get_hwnd('原神')))
        time.sleep(0.3)
        print('== 复查前台窗口：')
        dump_window(user32.GetForegroundWindow(), '  ')

    if chinese:
        print('== 强制把输入语言切回中文（键盘被留在英文时用这个）...')
        print('   结果:', force_chinese_input())
        time.sleep(0.3)
        print('== 复查前台窗口：')
        dump_window(user32.GetForegroundWindow(), '  ')


if __name__ == '__main__':
    main()
