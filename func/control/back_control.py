import time,win32gui,win32con,win32api
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
