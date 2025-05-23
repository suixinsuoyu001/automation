from func.common import *
from func.check import *
import pyautogui

import ctypes
import time

# 定义结构体（Windows API 需要）
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

# 定义鼠标事件常量
INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# 加载 user32.dll
user32 = ctypes.windll.user32

def click():
    # 创建鼠标按下事件
    inp_down = INPUT(type=INPUT_MOUSE)
    inp_down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN

    # 创建鼠标释放事件
    inp_up = INPUT(type=INPUT_MOUSE)
    inp_up.mi.dwFlags = MOUSEEVENTF_LEFTUP

    # 发送输入事件
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
    time.sleep(0.05)  # 模拟按住一段时间
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))



pyautogui.FAILSAFE = False  # 禁用 fail-safe

image_path = 'games/starRail/image/'
json_path = 'games/starRail/data/img_loc.json'

c = check('崩坏：星穹铁道',image_path,json_path)

def pic_click(names,matches):
    for i in names:
        if i in matches:
            pyautogui.click(matches[i][0])
            return

def pic_press(names,matches,s):
    for i in names:
        if i in matches:
            pyautogui.press(s)
            return

def talk():
    while True:
        click_names = ['任务标识','对话标识1', '对话标识3', '对话标识2', '消息标识','关闭消息','关闭1','教程翻页','教程翻页2',
                       '成就领取',  '再来一次', '领取', '传送', '前往', '确认2',

                       ]
        esc_names = ['空白位置1','阅读','获得物品']
        names = ['L','M']
        matches = c.check_pic(click_names+esc_names+names,0.85)
        focus = get_focus_window()
        if focus and '星穹铁道' in focus:
            print(matches)
            pic_click(click_names, matches)
            pic_press(esc_names, matches,'esc')
            if 'L' in matches or 'M' in matches:
                pyautogui.press(' ')
                click()



        time.sleep(0.2)

def mnyz():
    click_names = ['模拟宇宙_剧情下一步','模拟宇宙_剧情选择',
                   '确认1', '确认2', '确认3', '丢弃',
                   '模拟宇宙_选择选项',
                   '模拟宇宙_推荐祝福','模拟宇宙_未选标识','模拟宇宙_加权奇物','模拟宇宙_金血祝颂',
                   '模拟宇宙_祝福选择']
    esc_names = ['空白位置1', '空白位置2','空白位置4',]
    names = []
    while True:
        matches = c.check_pic(click_names+esc_names+names,0.85)
        focus = get_focus_window()
        if focus and '星穹铁道' in focus:
            print(matches)
            pic_click(click_names, matches)
            pic_press(esc_names, matches, 'esc')
            # pyautogui.press(' ')
        time.sleep(0.2)

def auto():
    click_names = ['活动1','活动3','活动4','活动5','hd6','hd7','hd8']
    esc_names = []
    names = []
    while True:
        matches = c.check_pic(click_names+esc_names+names,0.8)
        focus = get_focus_window()
        if focus and '星穹铁道' in focus:
            print(matches)
            pic_click(click_names, matches)
            pic_press(esc_names, matches, 'esc')
            pyautogui.press(' ')
        time.sleep(0.2)

if __name__ == '__main__':
    c.t_match.save_pic_loc('活动2',json_path,0.8)
    # print(res)
    # talk()
    # mnyz()