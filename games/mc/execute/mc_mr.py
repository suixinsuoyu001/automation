from games.mc.action.mc_task import *
import multiprocessing, time, pyautogui, os, signal
from pynput import keyboard

def 每日():
    c.check_start()
    mr()
    每日奖励()
    先约电台()
    change_zh()
    c.check_stop()

def run():
    每日()
    切换账号(3)
    每日()
    切换账号(4)
    每日()

if __name__ == '__main__':
    run()
