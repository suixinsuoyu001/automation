from games.starRail.action.bt_task2 import c
import multiprocessing, time, os, signal
import pynput
import pyautogui
import keyboard

terminate_flag = False


# 控制标志位
running_flag = False  # 默认开启节点
processes = []

import ctypes
import time
import re

# 定义 WinAPI 鼠标事件常量
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# 发送鼠标事件
def mouse_event(flags):
    ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)

# 左键按下
def left_down():
    mouse_event(MOUSEEVENTF_LEFTDOWN)

# 左键抬起
def left_up():
    mouse_event(MOUSEEVENTF_LEFTUP)

# 右键按下
def right_down():
    mouse_event(MOUSEEVENTF_RIGHTDOWN)

# 右键抬起
def right_up():
    mouse_event(MOUSEEVENTF_RIGHTUP)

def left_hold_click(t = 0.5):
    pyautogui.mouseDown(button='left')
    time.sleep(t)
    pyautogui.mouseUp(button='left')

def right_hold_click(t = 0.5):
    pyautogui.mouseDown(button='right')
    time.sleep(t)
    pyautogui.mouseUp(button='right')

def click_loop():
    pyautogui.press('q')
    time.sleep(1.5)
    while 1:
        print('等待按下v')
        # keyboard.wait('v')
        left_hold_click(0.25)
        left_down()
        time.sleep(0.15)
        right_down()
        time.sleep(0.1)
        left_up()
        time.sleep(0.05)
        right_up()
        left_down()
        time.sleep(0.15)
        right_down()
        time.sleep(0.4)
        left_up()
        time.sleep(0.05)
        right_up()
        time.sleep(0.5)

        print('操作结束')



# 定义进程1的函数
def worker1():
    global terminate_flag
    while not terminate_flag:
        click_loop()
        c.check_stop()


# 定义启动节点的函数（启动所有进程）
def start_node():
    global processes
    print("Starting processes...")
    p1 = multiprocessing.Process(target=worker1)
    processes.extend([p1])

    for process in processes:
        process.start()
        print(f"Started process PID: {process.pid}")


# 定义关闭节点的函数（杀死所有进程）
def stop_nodes():
    global processes
    print("Stopping all processes...")
    for process in processes:
        print(f"Terminating process PID: {process.pid}")
        os.kill(process.pid, signal.SIGTERM)  # 杀死进程
    processes.clear()


# 键盘监听函数
def on_press(key):
    global running_flag
    try:
        if hasattr(key, 'vk') and key.vk == 86:
            if running_flag:
                stop_nodes()
            else:
                start_node()
            running_flag = not running_flag
    except AttributeError:
        pass

def start():
    # 启动键盘监听器
    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()


if __name__ == '__main__':
    start()

