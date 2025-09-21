from games.starRail.action.bt_task import *

zhs = [
    'suixin001007@163.com', #0	流萤
    'suixin001006@163.com', #1	阿格莱雅
    'suixin001009@163.com', #2	希儿
    'suixin001001@163.com', #3	大黑塔
    '13280859317',          #4	黄泉
    'suixin001002@163.com', #5 	遐蝶
    'suixin001005@163.com', #6 	万敌
    'suixin001003@163.com', #7	龙丹
    'suixin001004@163.com', #8	暂无
    'suixin001008@163.com', #9	风堇
]

def mr():
    c.g_match.click(f'图标{resolution[0]}')
    每日(0, 'x存护2')			# 流萤 y11
    每日(1, 'x丰饶1')			# 阿格莱雅 y13
    每日(2, 'x毁灭1')		    # 希儿
    每日(3, 'x存护2')			# 大黑塔 y11
    每日(4, 'x存护2')			# 黄泉 y13
    每日(5, 'x存护2')			# 遐蝶 y12
    每日(6, 'x存护2')			# 万敌 y11
    每日(7, 'y11*')			# 龙丹
    每日(8, 'x毁灭特殊*')		# 暂无
    每日(9, 'x同谐2')			# 风堇 y11
    c.check_stop()

# x+行迹名 （x智识2）
# y1	冰套+风套		y2	物理套+击破套	y3	治疗套+普攻套
# y4	铁卫套+量子套	y5	防御套+雷套	y6	火套+虚数套
# y7	生命套+速度套	y8	追击套+dot套	y9	负面套+击破套
# y10	击破套+追击套	y11	增益套+战技套	y12	记忆套+量子套
# y13	治疗套+船长套

def mr_execute():
    log('执行开始')
    c.zhs = zhs
    # game_start(windows_title)
    mr()
    c.check_stop()



if __name__ == '__main__':
    mr_execute()
