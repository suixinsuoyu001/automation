from games.starRail.execute.bt_mr import mr_execute as bt_mr
from games.starRail.execute.bt_talk import bt_talk
from games.starRail.execute.bt_auto import bt_auto
from games.starRail.execute.bt_login import logins as bt_logins,login_one as bt_login_one
from games.ys.execute.ys_mr import run as ys_mr
from games.ys.execute.ys_talk import ys_talk
from games.ys.execute.ys_login import logins as ys_logins,login_one as ys_login_one
from games.mc.execute.mc_mr import run as mc_mr
from games.mc.execute.mc_jq import mc_talk


bt_zhs = [
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

ys_zhs = [
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
    # bt_logins()
    bt_login_one(5)
    # ys_logins()
    # ys_login_one(7)