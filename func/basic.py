from func.get_pic import *
import time,cv2,os
import subprocess
import pygetwindow as gw

def reset_pic(pic,width,height):
    return cv2.resize(pic, (width, height), interpolation=cv2.INTER_AREA)

def show_real_time_match():
    window_name = "Processed Screen"
    while True:

        t0 = time.time()
        # 获取并处理当前屏幕区域
        processed_screen = get_pic('原神')

        # processed_screen = cv2.resize(processed_screen, (1920, 1080), interpolation=cv2.INTER_AREA)
        # image = cv2.imread('screenshot2.png')
        # 显示处理后的图像
        processed_screen = reset_pic(processed_screen, 1600, 900)
        cv2.imshow(window_name, processed_screen)
        # set_window_topmost(window_name)  # 设置窗口置顶
        # 退出条件
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        end_time = time.time()
        print(f'总用时 {time.time() - t0}')
        # 控制每秒处理一次

    cv2.destroyAllWindows()

def open_file(exe_path, window_title):
    windows = gw.getWindowsWithTitle(window_title)
    print(windows)
    if windows:
        return
    timeout = 5  # 设置超时时间（秒）
    try:
        # 获取 exe 所在目录
        exe_dir = os.path.dirname(exe_path)

        # 启动程序，并将工作目录设置为 exe 所在目录
        process = subprocess.Popen(
            [exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=exe_dir  # 设置工作目录
        )

        start_time = time.time()
        while True:
            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                print(f"{window_title} 已成功运行！")
                break
            if time.time() - start_time > timeout:
                print(f"{window_title} 等待超时，程序未在 {timeout} 秒内启动。")
                process.terminate()
                break
            time.sleep(0.3)
    except FileNotFoundError:
        print(f"{exe_path} 文件未找到，请确认路径是否正确。")
    except Exception as e:
        print(f"运行 {exe_path} 时出错: {e}")

if __name__ == '__main__':
    # open_file(r'E:\python\pythonAuto\games\ys\tool\BetterGI\BetterGI.exe','更好的原神')
    import subprocess
    import os
    exe_path = r'E:\python\pythonAuto\games\ys\tool\BetterGI\BetterGI.exe'
    exe_dir = os.path.dirname(exe_path)
    subprocess.Popen([exe_path], cwd=exe_dir)