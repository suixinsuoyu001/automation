import ctypes
import time

# 定义鼠标事件的常量
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001

# 定义结构体 INPUT
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUT_UNION)]

# 调用 SendInput 函数
SendInput = ctypes.windll.user32.SendInput

def send_mouse_event(dx, dy):
    """底层调用 SendInput 的函数"""
    input_struct = INPUT(type=INPUT_MOUSE)
    input_struct.mi = MOUSEINPUT(
        dx=dx,
        dy=dy,
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE,
        time=0,
        dwExtraInfo=None,
    )
    SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(INPUT))

def smooth_mouse_move(dx, dy, duration=0.5, steps=40):
    """
    平滑鼠标移动
    :param dx: 水平移动距离（像素）
    :param dy: 垂直移动距离（像素）
    :param duration: 总移动时长（秒）
    :param steps: 平滑移动的步数
    """
    step_x = dx / steps
    step_y = dy / steps
    step_duration = duration / steps

    for _ in range(steps):
        send_mouse_event(int(step_x), int(step_y))
        time.sleep(step_duration)