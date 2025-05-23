import time

import keyboard

from games.ys.action.ys_action import *

def run(n = None):
    m.click('原神图标')
    c.check_start()
    if n is None:
        for i in zh:
            登录(i)
            log('等待0')
            keyboard.wait('0')
    else:
        登录(n)
    c.check_stop()

zh  = [
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
    run()