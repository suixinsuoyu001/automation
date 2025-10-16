import json,cv2,os,win32gui
import sys
import time
import traceback
import winreg
import win32con
import numpy as np
import pygetwindow as gw
import ctypes
from ctypes import wintypes
import psutil
import win32con
import win32process


def read_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        save = json.load(file)
        return save

file_path = os.path.dirname(__file__)
os.chdir(file_path.replace('func',''))
setting = read_json('setting.json')
resolution = setting['resolution']




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
            # if title and target_title in title:  # 模糊匹配
            if title and target_title == title:  # 绝对匹配
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


def log(*args, sep=' ', end='\n', file=None, flush=False, level=1):
    """
    level: 栈帧向上多少层（默认1是调用log的位置，2是调用者的调用者）
    """
    if file is None:
        file = sys.stdout

    # -1 是当前帧（log本身），-2 是 log 的调用者，-3 是再上层
    stack = traceback.extract_stack()
    if len(stack) >= level + 1:
        caller = stack[-(level + 1)]
        path = caller.filename
        line = caller.lineno
    else:
        path = '<unknown>'
        line = 0

    path_link = f'\033[34mFile "{path}", line {line}\033[0m'  # 蓝色
    content = sep.join(str(arg) for arg in args)

    print(f'{path_link} {content}', end=end, file=file, flush=flush)



def wake_screen():
    for i in range(3):
        # 模拟鼠标移动
        ctypes.windll.user32.mouse_event(1, 0, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(1, 20, 0, 0, 0)



def get_installed_games_with_path():
    uninstall_keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        # r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]

    res = []

    for root in roots:
        for key_path in uninstall_keys:
            try:
                reg_key = winreg.OpenKey(root, key_path)
                for i in range(winreg.QueryInfoKey(reg_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(reg_key, i)
                        subkey = winreg.OpenKey(reg_key, subkey_name)

                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]

                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0] if "InstallLocation" in [
                            winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0] if "DisplayIcon" in [
                            winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                        uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0] if "UninstallString" in [
                            winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""

                        # 综合判断 exe 的可能位置
                        exe_guess = ""
                        if display_icon and display_icon.lower().endswith(".exe"):
                            exe_guess = display_icon
                        elif uninstall_string and uninstall_string.lower().endswith(".exe"):
                            exe_guess = uninstall_string
                        elif install_location and os.path.isdir(install_location):
                            for file in os.listdir(install_location):
                                if file.lower().endswith(".exe") and "uninstall" not in file.lower():
                                    exe_guess = os.path.join(install_location, file)
                                    break

                        res.append((display_name, exe_guess))

                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        # 调试用，可移除
                        print(f"[!] 子项读取失败: {e}")
                        continue
            except Exception as e:
                # 调试用，可移除
                print(f"[!] 无法访问注册表路径: {key_path}, 错误: {e}")
                continue

    return res

def find_game_name(game_name):
    games = get_installed_games_with_path()
    for name, path in games:
        if game_name in name:
            print(f"{name}")

def get_game_path(game_name):
    games = get_installed_games_with_path()
    for name, path in games:
        if name != game_name:
            continue
        if game_name == '崩坏：星穹铁道':
            return path.replace('miHoYo Launcher\\launcher.exe','Star Rail\Game\StarRail.exe')
        elif game_name == '原神':
            return path.replace('miHoYo Launcher\\launcher.exe','Genshin Impact\Genshin Impact Game\YuanShen.exe')
        else:
            return path

def reset_pic(pic,width,height):
    return cv2.resize(pic, (width, height), interpolation=cv2.INTER_AREA)

def get_position(position):
    x = int(position[0]/2560*resolution[0])
    y = int(position[1]/1440*resolution[1])
    return x,y

def game_start(windows_title):
    hwnd = get_hwnd(windows_title)
    if hwnd:
        win32gui.ShowWindow(get_hwnd(windows_title), win32con.SW_RESTORE)  # 还原窗口（如果最小化了）
        win32gui.SetForegroundWindow(get_hwnd(windows_title))  # 激活窗口
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            log("SetForegroundWindow失败，尝试强制切换前台：", e)
            user32 = ctypes.windll.user32
            tid = win32process.GetWindowThreadProcessId(hwnd)[0]
            user32.AttachThreadInput(user32.GetCurrentThreadId(), tid, True)
            win32gui.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(user32.GetCurrentThreadId(), tid, False)
    else:
        log(get_game_path(windows_title))
        os.startfile(get_game_path(windows_title))
        while True:
            focus = get_focus_window()
            if focus and windows_title in focus:
                break

def close_exe(name):
    name += ".exe"
    for process in psutil.process_iter(['pid', 'name']):
        try:
            # 检查进程名称是否匹配
            if process.info['name'].lower() == name.lower():
                log(f"检测到程序进程: {name}, 正在关闭...")
                process.terminate()  # 终止进程
                process.wait(timeout=5)  # 等待进程完全关闭
                log(f"已成功关闭程序: {name}")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    log(f"未检测到程序进程: {name}")

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
    # wake_screen()