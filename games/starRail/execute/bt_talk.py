from games.starRail.action.bt_task import *
import multiprocessing, time, pyautogui, os, signal
from pynput import keyboard

terminate_flag = False


# 控制标志位
running_flag = True  # 默认开启节点
processes = []


# 定义进程1的函数
def worker1():
    global terminate_flag
    while not terminate_flag:
        talk()


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
            else:
                start_node()
            running_flag = not running_flag
    except AttributeError:
        pass


if __name__ == '__main__':
    # 启动进程（默认开启）
    start_node()

    # 启动键盘监听器
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    listener.join()