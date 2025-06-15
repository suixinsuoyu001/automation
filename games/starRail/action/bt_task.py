from datetime import datetime

from games.starRail.action.bt_func import check,windows_title,control,zhs
from func.common import *
import keyboard

c = check(windows_title)

phone_position = (29, 57)
yk_position = (1285, 1209)

def 登录(zh):
    login_wait = c.waits(['Enter','登出','登录其他账号'])
    if login_wait == 'Enter':
        while True:
            if c.waits(['Enter','注销']) == '注销':
                break
            c.hold_click(phone_position)
            time.sleep(1)
        c.wait_click('注销')
        c.wait_click('确认')
        c.click_until('登出', '退出')
        c.click_until('退出', '登录其他账号')
    if login_wait == '登出':
        c.click_until('登出','退出')
        c.click_until('退出', '登录其他账号')
    elif login_wait == '登录其他账号':
        pass
    c.wait_click('登录其他账号')
    c.wait_click('账号密码')
    c.text_input('输入账号', zh)
    c.text_input('输入密码', 'zxc147123')
    c.wait_click('同意')
    c.wait_click_limit('进入游戏')
    c.wait_click_limit('开始游戏')
    c.wait_click('点击进入')
    while True:
        res = c.waits_limit(['Enter','月卡标识'])
        if res == 'Enter':
            focus = get_focus_window()
            if focus and '星穹铁道' in focus:
                control.activate()
            break
        elif res == '月卡标识':
            while True:
                c.click_point(get_position(yk_position))
                if c.waits_limit(['Enter'], 0.5):
                    break
        c.send_key('i')

def logins():
    game_start(windows_title)
    control.hwnd = get_hwnd(windows_title)
    for zh in zhs:
        登录(zh)
        log('等待按下0')
        keyboard.wait('0')
    c.check_stop()

def login_one(n):
    game_start(windows_title)
    control.hwnd = get_hwnd(windows_title)
    登录(zhs[n])
    c.check_stop()


def 批量账号执行(fun1 = None ,fun2 = None, fun3 = None):
    game_start(windows_title)
    control.hwnd = get_hwnd(windows_title)
    for zh in zhs:
        登录(zh)
        if fun1:
            fun1()
        if fun2:
            fun2()
        if fun3:
            fun3()
    c.check_stop()
def 邮件领取():
    c.waits_limit(['Enter'])
    time.sleep(0.5)
    c.hold_click(phone_position)
    if c.waits(['邮件1','邮件2']) == '邮件1':
        c.wait_click('邮件1')
        c.wait_click('全部领取')
        c.wait_click('空白位置')
    返回主界面()

def 巡星之礼领取():
    c.waits(['Enter'])
    c.send_key('f1')
    while c.waits_limit(['领取2'],1):
        c.wait_click('领取2')
        c.wait_click('空白位置')
    c.send_key('esc')

def 返回主界面():
    while not c.waits_limit(['Enter'],0.5):
        c.send_key('esc')
    # control.activate()

def 抽卡兑换(flag = 1):
    c.waits(['Enter'])
    c.send_key('f3')
    c.wait_click('商店兑换')
    c.wait_click('余烬兑换')
    if c.waits_limit(['星轨专票'],1,0.95):
        c.wait_click('星轨专票')
        c.click('添加到最大')
        c.wait_click('确认')
        c.wait_click('空白位置')
    if flag and c.waits_limit(['星轨通票'],1,0.95):
        c.wait_click('星轨通票')
        c.click('添加到最大')
        c.wait_click('确认')
        c.wait_click('空白位置')
    返回主界面()

def 每月抽卡兑换():
    game_start(windows_title)
    control.hwnd = get_hwnd(windows_title)
    for zh in zhs:
        登录(zh)
        if '003' in zh or '004' in zh or '008' in zh or '009' in zh:
            抽卡兑换(0)
        else:
            抽卡兑换()
    c.check_stop()

def 战斗循环():
    c.click('挑战')
    if c.waits(['确认','开始挑战']) == '确认':
        return 返回主界面()
    c.click('开始挑战')
    while True:
        res = c.waits(['C', '再来一次','开拓力补充'],0.95)
        if res == 'C':
            c.click_point([2352, 66])
        elif res == '再来一次':
            c.click('再来一次')
        elif res == '开拓力补充':
            c.click('取消')
            c.click('取消')
            c.click('退出关卡')
            break
        time.sleep(1)
    返回主界面()

def 遗器(n):
    n = int(n)
    c.waits(['Enter'])
    c.send_key('f4')
    c.click(c.waits(['生存索引1','生存索引2']))
    c.move_click('拟造花萼金','侵蚀隧洞')
    c.move_wait('副本标识', f'遗器副本{n}')
    c.click_move_item(f'遗器副本{n}','进入')
    战斗循环()


def 行迹(name):
    c.waits(['Enter'])
    c.send_key('f4')
    c.click(c.waits(['生存索引1','生存索引2']))
    c.move_click('拟造花萼金','拟造花萼赤')
    c.move_wait('副本标识', f'行迹{name}')
    c.click_move_item(f'行迹{name}','进入')
    for i in range(6):
        c.click('+')
    战斗循环()

def 委托领取():
    now = datetime.now()
    c.waits(['Enter'])
    time.sleep(0.5)
    c.hold_click(phone_position)
    c.click('委托')
    if now.hour >=20:
        c.wait_click_limit('领取',0.5)
        c.wait_click_limit('再次派遣',0.5,0.9)
    else:
        c.wait_click_limit('一键领取',0.5)
        c.wait_click_limit('再次派遣',0.5,0.9)
    返回主界面()

def 合成():
    c.waits(['Enter'])
    time.sleep(0.5)
    c.hold_click(phone_position)
    c.click('合成')
    c.click('合成2')
    c.click('确认')
    返回主界面()

def 每日奖励():
    c.waits(['Enter'])
    time.sleep(0.5)
    c.send_key('f4')
    c.click(c.waits(['每日实训1','每日实训2']))

    while c.waits_limit(['领取3'],0.5):
        c.wait_click_limit('领取3',0.5)
        time.sleep(0.2)

    if c.waits(['每日奖励','每日奖励2']) == '每日奖励':
        c.click('每日奖励')
    else:
        if c.waits(['每日_合成']) == '每日_合成':
            返回主界面()
            合成()
            返回主界面()
            每日奖励()

    返回主界面()

def 无名勋礼():
    返回主界面()
    c.waits(['Enter'])
    time.sleep(0.5)
    c.send_key('f2')
    if c.waits(['无名勋礼任务1','无名勋礼任务2'],0.95) == '无名勋礼任务2':
        c.click('无名勋礼任务2')
        c.click('一键领取')
    res = c.waits(['无名勋礼奖励1', '无名勋礼奖励2','无名勋礼奖励3'],0.95)
    if res != '无名勋礼奖励1':
        c.click_until(res,'一键领取2')
        c.click('一键领取2')
    返回主界面()

def 每日(n,type):
    登录(zhs[n])
    邮件领取()
    if type.startswith('x'):
        行迹(type.replace('x',''))
    elif type.startswith('y'):
        遗器(type.replace('y',''))
    委托领取()
    每日奖励()
    无名勋礼()

if __name__ == '__main__':
    # game_start(windows_title)
    control.hwnd = get_hwnd(windows_title)
    c.save_pic_loc('开拓力补充',0.85)
    log('执行开始')
    # 每日(0,'x巡猎2')
    # 每日(1, 'y12')
    # 每日(2, 'x巡猎1')
    # 每日(3, 'y11')
    # 每日(4, 'y11')
    # 每日(5, 'x虚无2')
    # 每日(6, 'x虚无2')
    # 每日(9, 'y13')
    邮件领取()
    # 返回主界面()
    # 行迹('虚无2')
    # 遗器(11)
    # 委托领取()
    # 每日奖励()
    # 无名勋礼()
    c.check_stop()
