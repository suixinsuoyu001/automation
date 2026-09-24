import ctypes,math
import time,win32gui,win32con
from func.common import *
from pynput.mouse import Controller

# 复用 back_control 里的输入法(IME)屏蔽实现，
# 让原神/鸣潮这类走 func.check 的 c.control 也能直接调用 disable_ime_all / start_ime_watchdog
from func.control.back_control import (
    disable_ime, enable_ime, set_ime_english, disable_ime_all,
    close_ime, switch_to_english_layout,
    start_ime_watchdog, stop_ime_watchdog,
    force_english_input, enable_ime_all, write_text,
    set_window_input_english, restore_window_input,
    input_is_english, current_input_layout,
    force_chinese_input,
)


key_code = {
    'esc':win32con.VK_ESCAPE,
    'enter':win32con.VK_RETURN,
    'space':win32con.VK_SPACE,
    'shift':win32con.VK_LSHIFT,
    'f1':win32con.VK_F1,
    'f2':win32con.VK_F2,
    'f3':win32con.VK_F3,
    'f4':win32con.VK_F4
}


class Control():

    def __init__(self):
        self.hwnd = get_hwnd('鸣潮  ')
        # self.hwnd = 2820420
    def get_key_code(self,key):
        if type(key) == str and len(key) == 1:
            return ord(key.upper())
        elif key_code.get(key):
            return key_code.get(key)
        else:
            return key

    def send_key_down(self,key):
        mouse = Controller()
        last_position = mouse.position  # 记录鼠标初始位置
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYDOWN, self.get_key_code(key), 0)
        time.sleep(0.01)
        mouse.position = last_position

    def send_key_up(self,key):
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYUP, self.get_key_code(key), 0)

    def send_key(self,key,t = 0.1):
        self.send_key_down(key)
        time.sleep(t)
        self.send_key_up(key)


    def activate(self):
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_ACTIVATE, 1, 0)

    def inactivate(self):
        hwnd = self.hwnd  # 目标窗口句柄
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        foreground_thread = ctypes.windll.user32.GetWindowThreadProcessId(ctypes.windll.user32.GetForegroundWindow(),
                                                                          None)
        # 解除输入焦点绑定
        ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, False)
        # ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_INACTIVE, 0)


    def click(self,point):
        x, y = point  # 点击的坐标（相对于窗口客户区）
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

    def move(self):
        x, y = 500, 300  # 目标坐标

        # lParam = 低16位为x坐标，高16位为y坐标
        lParam = (y << 16) | x

        # 发送 WM_MOUSEMOVE 消息
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)

    # ==================== 输入法(IME)屏蔽相关 ====================
    # 与 func.control.back_control.Control 保持一致，方便各游戏用同一套调用方式
    def disable_ime(self):
        """屏蔽当前窗口的输入法（防止游戏内切换成中文输入法）"""
        return disable_ime(self.hwnd)

    def enable_ime(self):
        """恢复当前窗口的输入法"""
        return enable_ime(self.hwnd)

    def set_ime_english(self):
        """将当前窗口输入法强制切换为英文模式"""
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
        """启动输入法看门狗，持续强制英文输入（仅在游戏窗口处于前台时生效）"""
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




if __name__ == '__main__':
    c = Control()
    c.activate()
    c.click_mid()
    # c.move()

    # c.activate()
    # time.sleep(0.2)
