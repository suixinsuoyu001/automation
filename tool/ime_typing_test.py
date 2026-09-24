"""在原神登录界面上逐个试三种输入方式，直接看出哪种能把账号敲进输入框。

用法（游戏停在「输入账号」界面，命令行窗口能看见）：

    python tool/ime_typing_test.py test123@abc.com

流程：
    1. 提示你在 5 秒内用鼠标点一下游戏里的「输入账号」输入框（让光标进去）；
    2. 先执行一次窗口级输入法屏蔽(force_english_input)，并打印前后状态；
    3. 依次用三种方式打同一串字符，每打完一种都停下让你看输入框里到底是什么。

三种方式：
    A. SendInput + KEYEVENTF_UNICODE —— 绕过输入法（字符由系统直接送 WM_CHAR）
    B. 剪贴板 + Ctrl+V               —— 快捷键不是文字，输入法不会组词
    C. keyboard.write                —— 普通模拟按键（会经过输入法）

结论怎么看：
    * 如果第 2 步之后「输入法上下文」仍然是 有 —— 说明这台机器的输入法是 TSF
      类型（Win10/11 微软拼音就是），从别的进程用 IMM32 屏蔽不掉它，只能靠 A/B 绕过；
    * 把「A/B/C 哪个可行」告诉我，我就把登录改成那条路径。
"""
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ctypes

import keyboard
import win32clipboard
import win32gui
import win32process

from func.common import get_hwnd
from func.control.back_control import (
    enable_ime_all,
    force_english_input,
    imm32,
    input_is_english,
    restore_window_input,
    set_window_input_english,
    write_text,
)

TEXT = sys.argv[1] if len(sys.argv) > 1 else 'test123@abc.com'


def snap(label):
    user32 = ctypes.windll.user32
    fg = user32.GetForegroundWindow()
    try:
        title = win32gui.GetWindowText(fg)
        cls = win32gui.GetClassName(fg)
        tid, pid = win32process.GetWindowThreadProcessId(fg)
    except Exception:
        title = cls = '?'
        tid = pid = '?'
    ctx = 0
    try:
        ctx = imm32.ImmGetContext(fg)
        if ctx:
            imm32.ImmReleaseContext(fg, ctx)
    except Exception:
        pass
    layout = user32.GetKeyboardLayout(tid) if tid != '?' else 0
    print(f'[{label}] 前台: hwnd={fg} class={cls!r} pid={pid} '
          f'输入法上下文={"有" if ctx else "无"} 布局={hex(layout & 0xffffffff)} 标题={title!r}')


def clipboard_paste(text):
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()
    time.sleep(0.1)
    keyboard.send('ctrl+a')      # 先全选，覆盖输入框里已有的内容
    time.sleep(0.1)
    keyboard.send('ctrl+v')
    time.sleep(0.2)


def main():
    print(f'待测试文本: {TEXT}')
    print('请在 5 秒内用鼠标点一下游戏里的「输入账号」输入框，让光标进去 ...')
    for i in range(5, 0, -1):
        print('  ', i, flush=True)
        time.sleep(1)

    snap('开始')

    print('\n--- 0) force_english_input()：窗口级输入法屏蔽 ---')
    print('   结果:', force_english_input(get_hwnd('原神')))
    time.sleep(0.3)
    snap('0 之后')
    print('   >>> 若上面「输入法上下文」仍然是 有，说明本机输入法(IMM32)屏蔽不掉')

    print('\n--- 0b) set_window_input_english()：把输入语言临时切成英文（登录用的就是这招）---')
    print('   结果:', set_window_input_english())
    time.sleep(0.3)
    snap('0b 之后')
    print('   >>> 关键：若「布局」变成了英文(如 0x4090409)，说明窗口接受了切换；')
    print('       若「布局」还是 0x8040804(中文)，说明该游戏忽略了 WM_INPUTLANGCHANGEREQUEST。')
    print('   当前是否有英文输入语言(决定用哪种输入方式):', input_is_english())

    print('\n--- A) SendInput + KEYEVENTF_UNICODE（绕过输入法，但可能带出输入法状态条）---')
    n = write_text(TEXT, delay=0.02)
    print(f'   注入字符数: {n}/{len(TEXT)}')
    input('   看清游戏输入框里的内容 / 有没有弹出输入法后，按回车继续 ...')
    snap('A 之后')

    print('\n--- B) 剪贴板 + Ctrl+V ---')
    try:
        clipboard_paste(TEXT)
        print('   已发送 Ctrl+A / Ctrl+V')
    except Exception as e:
        print('   失败:', e)
    input('   看清游戏输入框里的内容 / 有没有弹出输入法后，按回车继续 ...')
    snap('B 之后')

    print('\n--- C) keyboard.write（英文布局下不会经过输入法）---')
    print('   当前是否有英文输入语言:', input_is_english())
    keyboard.send('ctrl+a')
    time.sleep(0.1)
    keyboard.write(TEXT, delay=0.02)
    input('   看清游戏输入框里的内容 / 有没有弹出输入法后，按回车结束 ...')
    snap('C 之后')

    print('\n== 请告诉我三件事：')
    print('   1) 0b 之后「布局」有没有变成英文(0x4090409)？')
    print('   2) A / B / C 哪一种打进去的字符正确？')
    print('   3) A / B / C 哪一种**没有**弹出中文输入法状态条？')
    print('== 需要恢复时运行： python tool/ime_diagnose.py --restore')
    restore_window_input()
    enable_ime_all(get_hwnd('原神'))


if __name__ == '__main__':
    main()
