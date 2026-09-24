from games.starRail.action.bt_task import *
import keyboard

def login_one(n):
    c.zhs = zhs
    # game_start(windows_title)
    c.g_match.click(f'图标{resolution[0]}')
    登录(c.zhs[n])
    c.check_stop()

def logins():
    c.zhs = zhs
    # game_start(windows_title)
    c.g_match.click(f'图标{resolution[0]}')
    # 屏蔽游戏窗口的中文输入法，防止登录时切换成中文输入
    c.control.disable_ime_all()
    # 启动输入法看门狗：仅在游戏窗口处于前台时强制英文输入，
    # 切出游戏后不影响其他程序正常输入中文
    c.control.start_ime_watchdog()
    for zh in c.zhs:
        登录(zh)
        # 邮件领取()
        # 巡星之礼领取()
        # 兑换码()
        if c.is_focus():
            c.control.activate()
        # 每次登录前再次屏蔽输入法，避免被系统重新关联
        c.control.disable_ime_all()
        log('等待按下0')
        keyboard.wait('0')
    c.control.stop_ime_watchdog()
    c.check_stop()





zhs = [
    'suixin001007@163.com', #0	流萤
    'suixin001006@163.com', #1	阿格莱雅
    'suixin001001@163.com', #2	大黑塔
    '13280859317',          #3	黄泉
    'suixin001002@163.com', #4 	遐蝶
    'suixin001005@163.com', #5 	万敌
    'suixin001008@163.com', #6	风堇
    'suixin001009@163.com', #7	希儿
    'suixin001003@163.com', #8	龙丹
    'suixin001004@163.com', #9	暂无
]

if __name__ == '__main__':
    logins()
    # login_one(2)

