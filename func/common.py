import json,cv2,os,win32gui
import time

import numpy as np
import pygetwindow as gw
import ctypes
from ctypes import wintypes

file_path = os.path.dirname(__file__)
os.chdir(file_path.replace('func',''))

def read_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        save = json.load(file)
        return save

def save_json(path,data):
    with open(path, 'w', encoding='utf-8') as file:
        # 使用 json.dump 将数据写入文件
        json.dump(data, file, ensure_ascii=False, indent=4)  # 设置 indent=4 来格式化输出

def load_image_with_zh_path(file_path):
    with open(file_path, 'rb') as f:
        binary_data = f.read()
    image_data = np.frombuffer(binary_data, dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image is None:
        print(f"无法加载图片: {file_path}")
        return None
    return image


def get_focus_window():
    # 获取当前焦点窗口
    focus_window = gw.getActiveWindow()

    if focus_window:
        return focus_window.title
    else:
        pass
        # print("没有获取到焦点窗口")

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

def enum_all_windows():
    def callback(hwnd, extra):
        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)
        # 获取窗口类名
        class_name = win32gui.GetClassName(hwnd)
        # 判断窗口是否可见
        visible = win32gui.IsWindowVisible(hwnd)

        print(f"窗口句柄: {hwnd}, 标题: {title}, 类名: {class_name}, 可见: {visible}")

    win32gui.EnumWindows(callback, None)


def get_item_hwnd(right, bot):
    result = ""
    def callback(hwnd, extra):
        nonlocal result  # 让回调函数可以修改外部变量
        if win32gui.IsWindowVisible(hwnd):  # 只查找可见窗口
            title = win32gui.GetWindowText(hwnd)
            sp_left, sp_top, sp_right, sp_bot = win32gui.GetClientRect(hwnd)
            if sp_right == right and sp_bot == bot:
                result = hwnd
    win32gui.EnumWindows(callback, None)
    return result if result else None



if __name__ == '__main__':
    path = 'E:\python\pythonAuto\data\img_loc.json'
    # 16384554
    # print(get_hwnd('鸣潮'))
    enum_all_windows()
    # time.sleep(3)
    # # 获取 user32 函数
    # user32 = ctypes.WinDLL('user32')
    # user32.GetForegroundWindow.argtypes = []
    # user32.GetForegroundWindow.restype = wintypes.HWND
    #
    # # 获取当前活动窗口句柄
    # hwnd = user32.GetForegroundWindow()
    # print(hwnd)