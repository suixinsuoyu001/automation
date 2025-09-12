from games.mc.action.mc_task import g_match,c,每日
from games.mc.action.ok import open_ok_ww,close_ok_ww
import multiprocessing, time, pyautogui, os, signal
from pynput import keyboard


def run():
    g_match.click('鸣潮图标')
    c.check_start()
    pid = open_ok_ww()
    每日(1, 凝素领域='佩枪2')
    每日(2, 凝素领域='佩枪2')
    每日(3, 凝素领域='佩枪2')
    c.check_stop()
    close_ok_ww(pid)


if __name__ == '__main__':
    run()
