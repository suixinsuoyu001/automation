import ctypes
from pywinauto import Application
import time,win32gui,win32con,win32api
from pywinauto import Desktop

def get_current_foreground_window():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    return hwnd
get_current_foreground_window()
def get_hwnd(target_title: str) -> str:
    result = ""
    def callback(hwnd, extra):
        nonlocal result  # 让回调函数可以修改外部变量
        if win32gui.IsWindowVisible(hwnd):  # 只查找可见窗口
            title = win32gui.GetWindowText(hwnd)
            if title and target_title in title:  # 模糊匹配
                result = hwnd

    win32gui.EnumWindows(callback, None)
    return result if result else None

def activate():
    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)

def inactivate():
    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_INACTIVE, 0)

hwnd = get_hwnd('鸣潮')
# 定义常量
WM_KEYDOWN = 0x0100  # 按键按下消息
WM_KEYUP = 0x0101    # 按键释放消息

# 定义虚拟键码
VK_W = 0x57  # 'W' 键的虚拟键码
VK_ESCAPE = 0x01
# 使用 ctypes 调用 PostMessage 向窗口发送消息
def send_key(hwnd, key_code, msg_type):
    ctypes.windll.user32.PostMessageW(hwnd, msg_type, key_code, 0)

def esc():
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    # win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)


def click( x= 0, y = 0):
    x = x if isinstance(x, int) else int(x)
    y = y if isinstance(y, int) else int(y)
    long_position = win32api.MAKELONG(x, y)
    win32gui.PostMessage(
        hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position
    )  # 鼠标左键按下
    time.sleep(0.2)
    win32gui.PostMessage(
        hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position
    )  # 鼠标左键抬起
    time.sleep(0.1)


# 鼠标点击坐标（相对于窗口客户区）
x, y = 1196, 1324

# 计算 `lParam`（低位存X，高位存Y）
lParam = (y << 16) | x
WM_ACTIVATE = 0x0006  # 激活窗口的消息
ctypes.windll.user32.PostMessageW(hwnd, WM_ACTIVATE, 1, 0)
esc()

# 发送鼠标左键释放
# win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
# win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
# time.sleep(2)


time.sleep(1)
# win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_INACTIVE, 0)



