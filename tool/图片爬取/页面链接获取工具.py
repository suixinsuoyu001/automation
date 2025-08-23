import pyautogui
import pyperclip
import time

import multiprocessing, time, pyautogui, os, signal
from pynput import keyboard

terminate_flag = False


# 控制标志位
running_flag = True  # 默认开启节点
processes = []

n = 1
arr = []
def 切换下一标签页():
    start_x, start_y = 500, 500
    pyautogui.moveTo(start_x, start_y)
    pyautogui.mouseDown(button='right')
    pyautogui.moveTo(start_x, start_y - 200, duration=0.01)
    pyautogui.moveTo(start_x - 200, start_y - 200, duration=0.01)
    pyautogui.mouseUp(button='right')

def 复制当前页面链接():
    global n
    global arr
    print(n)
    pyautogui.click(1552, 93)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.hotkey('ctrl', 'c')
    copied_text = pyperclip.paste()
    if copied_text in arr:
        time.sleep(0.8)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'c')
        copied_text = pyperclip.paste()
    arr.append(copied_text)
    if len(set(arr)) != n:
        return 1
    n += 1

    with open('3.txt', 'a', encoding='utf-8') as file:
        file.write(copied_text + '\n')

# 定义进程1的函数
def worker1():
    global terminate_flag
    while not terminate_flag:
        res = 复制当前页面链接()
        if res:
            break
        切换下一标签页()


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
        if hasattr(key, 'vk') and key.vk == 97:
            if running_flag:
                stop_nodes()
                global arr
                arr.clear()
            else:
                start_node()
            running_flag = not running_flag
    except AttributeError:
        pass


if __name__ == '__main__':
    time.sleep(1)
    # 启动进程（默认开启）
    start_node()

    # 启动键盘监听器
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    listener.join()

