import time

from games.ys.action.ys_action import *



def logins():
    game_start(windows_title)
    c.check_start()
    for zh in zhs:
        # if zh in [zhs[4],zhs[5]]:
        #     continue
        登录(zh)
        # 兑换码()
        log('等待按下0')
        keyboard.wait('0')
    c.check_stop()

def login_one(n):
    game_start(windows_title)
    c.check_start()
    登录(zh[n])
    c.check_stop()

zhs = [
        'kechengzhuang524@126.com',     #0
        'kemeihao694350@126.com',       #1
        'kenc40sklx6093@126.com',       #2
        'suixin001005@163.com',         #3
        'suixin001002@163.com',         #4
        'kengfeiyan34534@126.com',      #5
        'k6597975255692@sohu.com',      #6
        '13280859317'                   #7
       ]







if __name__ == '__main__':

    # logins()
    login_one(5)
