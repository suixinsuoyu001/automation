from games.starRail.action.bt_task import *
import keyboard



def login_one(n):
    c.zhs = zhs
    game_start(windows_title)
    登录(c.zhs[n])
    c.check_stop()

def logins():
    c.zhs = zhs
    game_start(windows_title)
    for zh in c.zhs:
        登录(zh)
        # 邮件领取()
        # 巡星之礼领取()
        # 兑换码()
        if c.is_focus():
            c.control.activate()
        log('等待按下0')
        keyboard.wait('0')
    c.check_stop()

zhs = [
    'suixin001007@163.com', #0
    'suixin001006@163.com', #1
    'suixin001009@163.com', #2
    'suixin001001@163.com', #3
    '13280859317',          #4
    'suixin001005@163.com', #5
    'suixin001002@163.com', #6
    'suixin001003@163.com', #7
    'suixin001004@163.com', #8
    'suixin001008@163.com', #9
]

if __name__ == '__main__':
    logins()
    # login_one(1)
