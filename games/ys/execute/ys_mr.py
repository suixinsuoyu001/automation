import time

from games.ys.action.ys_action import *


if __name__ == '__main__':
    # 打开betterGi()
    # m.click('原神图标2')
    # m.wait('退出登录')
    # c.check_start()
    # # 登录(zh[0])
    #
    # 每日(1)
    #
    # # 圣遗物分解()
    # c.check_stop()
    import subprocess

    # 替换为你的exe文件路径
    exe_path = r"E:\python\automation\games\ys\tool\betterGi\BetterGI.exe"

    # 打开exe文件
    subprocess.Popen(exe_path)