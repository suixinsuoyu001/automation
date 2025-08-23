import subprocess
import os
import time

import pyautogui
from games.mc.data.mc_data import *



def open_ok_ww():
    python_exe = os.path.join(ok_ww_path, "venv", "Scripts", "python.exe")
    script_path = os.path.join(ok_ww_path, script_name)

    process = subprocess.Popen(
        [python_exe, script_path],
        cwd=ok_ww_path,
        stdout=None,  # 继承控制台
        stderr=None
    )
    time.sleep(5)
    return process.pid

def close_ok_ww(pid):
    os.system(f"taskkill /PID {pid} /F")


if __name__ == '__main__':
    pid = open_ok_ww()
    pyautogui.press('f9')
