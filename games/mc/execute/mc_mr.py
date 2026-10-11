from games.mc.action.mc_task import c,每日
from games.mc.action.ok import open_ok_ww,close_ok_ww
import multiprocessing, time, pyautogui, os, signal
from pynput import keyboard


def run(flag = 1):
    # 窗口已经在 -> 只置前；不在 -> 点一次「鸣潮图标」启动（绝不会连点两次）
    c.focus_or_start_game()
    c.check_start()
    pid = None
    if flag == 1:
        pid = open_ok_ww()
    # 每日(1, 凝素领域='',无音清剿='隐喙深腹')
    # 每日(2, 凝素领域='佩枪2',无音清剿='')
    每日(2, 凝素领域='', 无音清剿='隐喙深腹')
    每日(3, 凝素领域='', 无音清剿='隐喙深腹')
    每日(1, 凝素领域='长刃3',无音清剿='')
    # 每日(2, 凝素领域='长刃3',无音清剿='')
    # 每日(3, 凝素领域='佩枪3',无音清剿='')
    c.check_stop()
    if flag == 1:
        close_ok_ww(pid)


if __name__ == '__main__':
    run(2)

