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


# ---------------------------------------------------------------------------
# 「把游戏启动起来」的安全实现（原神 / 崩铁 / 鸣潮共用）
#
# 背景：原神和崩铁共用一个**单实例**启动器。如果短时间内被拉起两次
# （典型场景：任务入口先点了一次桌面图标，紧接着 check_start 又点了一次），
# 启动器会直接弹
#     Multiple games are detected. Please exit the existing client.
#     Error Code:(3,0,0)
# 对话框一出来游戏就再也起不来，任务只能卡死在「等待窗口」上。
#
# 所以「点桌面图标启动游戏」统一走 start_game_if_missing()，由它保证：
#   * 窗口已经在     -> 调用方先判断，根本不会点（点图标 = 又拉起一个启动器）
#   * 刚点过一次图标 -> GAME_START_COOLDOWN 秒内不再点（游戏正在启动）
#   * 游戏进程已经在 -> 说明正在启动（窗口还没画出来），不点，继续等窗口
#   * 启动器进程在跑 -> 说明正在启动（只是窗口还没出来），先等窗口出来再决定
#   * 上面都没命中   -> 只留 GAME_START_GRACE（0.3 秒）确认一下，然后点图标
#
# 为什么不做「干等 5 秒」：查窗口（EnumWindows）和查进程（psutil 走一圈
# 只 ~28ms）都是确定性的即时信号，比盲等可靠也快得多；实测冷启动时
# 「判断 + 点击图标」现在总共只花 ~0.35 秒。
# ---------------------------------------------------------------------------

GAME_START_COOLDOWN = 150    # 两次「点桌面图标」之间的最小间隔（秒）
GAME_START_GRACE = 0.3       # 点图标前盯窗口的时间（秒）：只要窗口自己冒出来就不点
GAME_START_POLL = 0.04       # 观察期内查窗口的间隔（秒，EnumWindows 很便宜）
GAME_START_LAUNCHER_GRACE = 2.5   # 发现「启动器正在跑但窗口还没出来」时的追加等待（秒）

# 米哈游启动器（原神/崩铁共用同一个单实例启动器）：
# 进程名 launcher.exe 太通用，所以按**完整路径**里的安装目录来认，
# 例如 D:\miHoYo Launcher\launcher.exe -> 命中 'mihoyo launcher'。
MHY_LAUNCHER_PATH = 'mihoyo launcher'

# 窗口标题 -> 上一次成功点桌面图标的时间。按标题存，所以各模块各自 new
# 出来的 check 实例共享同一份状态，不会「你点一次我再点一次」。
_game_started_at = {}


def game_process_running(exe_names):
    """游戏**本体**进程是否已经在运行（窗口可能还没画出来）。

    exe_names 里写进程名片段即可（小写比较），例如 ``('yuanshen.exe',)``；
    传空 / None 表示不做这项判断（只靠窗口 + 宽限判断）。

    实测 300+ 进程的机器上走一圈约 28ms，比「盲等几秒」划算得多。
    """
    names = [n.lower() for n in (exe_names or ()) if n]
    if not names:
        return False
    try:
        for process in psutil.process_iter(['name']):
            name = (process.info.get('name') or '').lower()
            if name and any(n in name for n in names):
                return True
    except Exception as e:
        # 查询进程失败不能影响任务：当作「没检测到」处理
        log(f'game_process_running: 查询进程失败，忽略本次判断（{e}）')
    return False


def launcher_running(path_hint = MHY_LAUNCHER_PATH):
    """米哈游启动器是否正在运行（窗口可能还没出来）。

    只看名字 ``launcher.exe`` 太容易误判（别的软件也用这个名字），所以要求
    **exe 路径**里有 ``miHoYo Launcher`` 目录。读不到路径（权限不足）就当没
    命中 —— 漏判只会退回到「短观察期后照常点图标」，不会把任务卡死。
    """
    try:
        for process in psutil.process_iter(['name']):
            if (process.info.get('name') or '').lower() != 'launcher.exe':
                continue
            try:
                exe = (process.exe() or '').lower()
            except Exception:
                continue
            if path_hint in exe:
                return True
    except Exception as e:
        log(f'launcher_running: 查询进程失败，忽略本次判断（{e}）')
    return False


def start_game_if_missing(windows_title, g_match, icon = None, exe = None, timeout = 60):
    """游戏窗口不在时，点桌面上的游戏图标把游戏启动起来。

    **绝不会连点两次**（原因见上面的大段注释），也只记日志、**不抛异常** ——
    图标模板不存在、桌面上找不到图标（被其它窗口挡住 / 不在当前显示器）时
    返回 False，调用方照常继续等窗口。

    判断顺序（前三条都是即时的，最后才是 0.3 秒的短观察期）::

        窗口已在 / 刚点过 / 游戏进程在跑 / 启动器进程在跑  -> 不点
        否则 -> 盯 GAME_START_GRACE 秒（窗口冒出来就不点）-> 再确认一次进程 -> 点

    :param g_match: func.control.global_match.match 实例（全屏找图 + 点击）
    :param icon:    桌面图标模板名，默认「图标 + 屏幕宽」（原神/崩铁的约定）
    :param exe:     游戏本体进程名片段，例如 ('yuanshen.exe',)
    :return: 本次是否真的点了桌面图标
    """
    icon = icon or f'图标{resolution[0]}'
    now = time.time()
    last = _game_started_at.get(windows_title)
    if last and now - last < GAME_START_COOLDOWN:
        log(f'{windows_title} {int(now - last)}s 前刚点过桌面图标「{icon}」，'
            f'不再重复点击（重复启动会弹「Multiple games are detected」）')
        return False
    if get_hwnd(windows_title):
        log(f'{windows_title} 窗口已经在，不点桌面图标')
        return False
    if game_process_running(exe):
        log(f'{windows_title} 进程已经在运行（窗口还没出来），不点桌面图标，继续等窗口')
        return False

    # 短观察期：用户可能刚好双击过图标（启动器还在起来），这期间一旦窗口
    # 出现就放弃点击 —— 不盲等，只花 GAME_START_GRACE（默认 0.3 秒）。
    deadline = now + GAME_START_GRACE
    extended = False
    while True:
        if get_hwnd(windows_title):
            log(f'{windows_title} 窗口已出现，不点桌面图标')
            return False
        if time.time() >= deadline:
            # 启动器进程在跑但窗口还没出来：它在启动（正常几百毫秒后就有窗口），
            # 也可能是被用户缩到托盘里了。再给 GAME_START_LAUNCHER_GRACE 秒，
            # 超时就照常点图标，绝不无限等。
            if not extended and launcher_running():
                log('检测到米哈游启动器正在运行（窗口还没出来），'
                    f'再等 {GAME_START_LAUNCHER_GRACE:g} 秒看窗口会不会自己出现')
                deadline = time.time() + GAME_START_LAUNCHER_GRACE
                extended = True
                continue
            break
        time.sleep(GAME_START_POLL)
    # 观察期结束再确认一次：用户双击后游戏本体进程可能刚好起来了
    if game_process_running(exe):
        log(f'{windows_title} 进程已经开始运行，不点桌面图标，继续等窗口')
        return False

    try:
        clicked = g_match.click(icon, timeout = timeout)
    except FileNotFoundError as e:
        log(f'找不到桌面图标模板「{icon}」（{e}），跳过自动启动，改为等待窗口')
        return False
    if clicked:
        _game_started_at[windows_title] = time.time()
        log(f'已点击桌面图标「{icon}」，等待 {windows_title} 窗口出现')
    return clicked




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