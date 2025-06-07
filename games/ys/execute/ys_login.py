import time

from games.ys.action.ys_action import *

zh = [
        'kechengzhuang524@126.com',     #0
        'kemeihao694350@126.com',       #1
        'kenc40sklx6093@126.com',       #2
        'suixin001005@163.com',         #3
        'suixin001002@163.com',         #4
        'kengfeiyan34534@126.com',      #5
        'k6597975255692@sohu.com',      #6
        '13280859317'                   #7
       ]

def run():
    m.click('原神图标2')
    # 登录(zh[0])
    # 登录(zh[1])
    # 登录(zh[2])
    # 登录(zh[3])
    # 登录(zh[4])
    # 登录(zh[5])
    登录(zh[6])
    # 登录(zh[7])

    c.check_stop()

if __name__ == '__main__':
    c.check_start()
    # # 登录(zh[0])
    # 邮件领取()
    # # 每日(0,1)
    # #
    # # # 圣遗物分解()
    # c.check_stop()
    run()