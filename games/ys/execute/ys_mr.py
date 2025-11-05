import time

from games.ys.action.ys_action import *

# 1 纳塔套
# 2 生命之契燃烧套
# 3 枫丹套
# 4 层岩套
# 5 下落套
# 6 挪德卡莱套

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
    # 打开betterGi2()
    c.g_match.click(f'图标{resolution[0]}')
    # game_start(windows_title)
    c.check_start()
    每日(0, 1)
    每日(1, 5)
    每日(2, 6)
    每日(3, 5)
    每日(4, 1)
    每日(5, 1)
    每日(6, 6)
    每日(7, 6)
    c.check_stop()

def run2():
    game_start(windows_title)
    c.check_start()
    每日2(0,1)
    每日2(1,1)
    每日2(2,1)
    每日2(3,1)
    每日2(4,1)
    每日2(5,1)
    每日2(6,1)
    每日2(7,1)
    c.check_stop()

if __name__ == '__main__':

    # # 登录(zh[0])
    # 邮件领取()
    # # 每日(0,1)
    # run()
    run2()
