from games.starRail.action.bt_task import *

zhs = [
    'suixin001007@163.com', #0
    'suixin001006@163.com', #1
    'suixin001009@163.com', #2
    'suixin001001@163.com', #3
    '13280859317',          #4
    'suixin001002@163.com', #5
    'suixin001005@163.com', #6
    'suixin001003@163.com', #7
    'suixin001004@163.com', #8
    'suixin001008@163.com', #9
]

def mr():
    game_start(windows_title)
    每日(0, 'y11')
    每日(1, 'y13')
    每日(2, 'x毁灭1')
    每日(3, 'y11')
    每日(4, 'y13')
    每日(5, 'y12')
    每日(6, 'y11')
    每日(7, 'y11*')
    每日(8, 'x毁灭特殊*')
    每日(9, 'y11')
    c.check_stop()

# x+行迹名 （x智识2）
# y1	冰套+风套		y2	物理套+击破套	y3	治疗套+普攻套
# y4	铁卫套+量子套	y5	防御套+雷套	y6	火套+虚数套
# y7	生命套+速度套	y8	追击套+dot套	y9	负面套+击破套
# y10	击破套+追击套	y11	增益套+战技套	y12	记忆套+量子套
# y13	治疗套+船长套

if __name__ == '__main__':
    log('执行开始')

    c.zhs = zhs
    game_start(windows_title)

    mr()
    c.check_stop()
