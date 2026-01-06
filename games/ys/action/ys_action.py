import time

from func.common import *
from func.check import *
from func.control.global_match import *
from func.control.mouse_move import *
from games.ys.action.ys_funtion import *
from games.ys.match.yolo_match import *
import pyautogui
import keyboard
import subprocess

pyautogui.FAILSAFE = False  # 禁用 fail-safe

image_path = 'games/ys/image/'
json_path = 'games/ys/data/img_loc.json'

AutoFight = read_json('games/ys/data/AutoFight.json')

windows_title = '原神'

with open('games/ys/data/兑换码.txt', "r", encoding="utf-8") as fp:
    codes = [line.strip() for line in fp]
fp.close()

c = check(windows_title,image_path,json_path)
m = match(image_path,0.9)

num = 0.85

原粹树脂使用坐标 = (1686, 658)
浓缩树脂使用坐标 = (1683, 815)


def click(name, num=num):
    if c.processed_screen is None:
        log('check_start未运行')
        return
    log(f'click:{name} 开始捕获',level=2)
    while True:
        focus = get_focus_window()
        position = c.check_one_pic(name, num, c.processed_screen)
        if focus and '原神' in focus and position:
            log(position)
            pyautogui.click(get_position(position[0]))
            time.sleep(0.4)
            break
        time.sleep(0.02)
    log(f'click:{name} 已捕获并点击',level=2)

def move(name, num=num):
    if c.processed_screen is None:
        log('check_start未运行')
        return
    log(f'click:{name} 开始捕获',level=2)
    while True:
        focus = get_focus_window()
        position = c.check_one_pic(name, num, c.processed_screen)
        if focus and '原神' in focus and position:
            pyautogui.moveTo(get_position(position[0]))
            time.sleep(0.4)
            break
        time.sleep(0.02)
    log(f'click:{name} 已捕获并点击',level=2)

def click_limit(name,t,num = num):
    if c.processed_screen is None:
        log('check_start未运行')
        return
    log(f'click_limit:{name} 开始捕获',level=2)
    start_time = time.time()
    while True:
        c.control.activate()
        position = c.check_one_pic(name, num, c.processed_screen)
        if position is not None:
            pyautogui.click(get_position(position[0]))
            time.sleep(0.4)
            log(f'click_limit:{name} 已捕获并点击',level=2)
            break
        time.sleep(0.02)
        if time.time() - start_time > t:
            log(f'click_limit:{name} 未捕获，超时取消',level=2)
            break

def waits(names,num = num):
    log(f'waits:{names} 开始捕获',level=2)
    while c.processed_screen is None:
        log('check_start未运行')
    while True:
        focus = get_focus_window()
        if not (focus and '原神' in focus):
            continue
        for name in names:
            position = c.check_one_pic(name,num,c.processed_screen)
            if position:
                log(f'wait: {name} 已找到',level=2)
                time.sleep(0.2)
                return name

def waits_limit(names,t = 0.5,num = num):
    log(f'waits_limit:{names} 开始捕获',level=2)
    while c.processed_screen is None:
        log('check_start未运行')
    t1 = time.time()
    while True:
        focus = get_focus_window()
        if not (focus and '原神' in focus):
            continue
        for name in names:
            position = c.check_one_pic(name,num,c.processed_screen)
            if position:
                log(f'wait: {name} 已找到',level=2)
                time.sleep(0.2)
                return name
        t2 = time.time() - t1
        if t2 > t:
            break

def waits_many(names,num = num):
    log(f'waits:{names} 开始捕获',level=2)
    while c.processed_screen is None:
        log('check_start未运行')
    res = []
    position = None
    while position is None:
        focus = get_focus_window()
        if not (focus and '原神' in focus):
            continue
        for name in names:
            if position is None:
                position = c.check_one_pic(name,num,c.processed_screen)
    for name in names:
        position = c.check_one_pic(name, num, c.processed_screen)
        if position:
            res.append(name)
    return res

def waits_speed(names,num = num):
    log(f'waits:{names} 开始捕获',level=2)
    while c.processed_screen is None:
        log('check_start未运行')
    while True:
        focus = get_focus_window()
        if not (focus and '原神' in focus):
            continue
        for name in names:
            position = c.check_one_pic(name,num,c.processed_screen)
            if position:
                log(f'wait: {name} 已找到',level=2)
                return name

def waits_check_speed(names,num = num):
    log(f'waits:{names} 开始捕获',level=2)
    while c.processed_screen is None:
        log('check_start未运行')
    focus = get_focus_window()
    if not (focus and '原神' in focus):
        return None
    for name in names:
        position = c.check_one_pic(name,num,c.processed_screen)
        if position:
            log(f'wait: {name} 已找到',level=2)
            return name

def scroll_click(name1,name2,num = num):
    while 1:
        match = c.match_one_pic(name1, num)
        if match:
            log(f'scroll_click:已识别{name1}',level=2)
            break
        for i in range(8):
            pyautogui.scroll(-5)
        time.sleep(0.5)
    matches = c.match_pics(name2,num)
    log(match)
    log(matches)
    for i in matches:
        if match[0][1]<i['y']+100:
            pyautogui.click(get_position([i['x'],i['y']]))
            break

    log(f'scroll_click:已识别{name2}并点击',level=2)




def get_ego_angle():
    c.model_loop_start()
    pyautogui.middleClick()
    if 270 > c.ego_angle > 90:
        pyautogui.press('s')
        time.sleep(0.2)
        pyautogui.middleClick()
        time.sleep(0.6)
    while True:
        if c.size_diff and 300 > abs(c.size_diff):
            time.sleep(0.1)
            pyautogui.press('w')
            time.sleep(1)
            ego_angle = c.ego_angle
            log(c.ego_angle, c.size_diff)
            if 90 > ego_angle > 30:
                pyautogui.keyDown('d')
                time.sleep(0.2)
                pyautogui.rightClick()
                time.sleep(0.2)
                pyautogui.keyUp('d')
            elif 330 > ego_angle > 270:
                pyautogui.keyDown('a')
                time.sleep(0.2)
                pyautogui.rightClick()
                time.sleep(0.2)
                pyautogui.keyUp('a')
            else:
                pyautogui.keyDown('w')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.5)
                pyautogui.keyUp('shift')
                break
        if c.ego_angle > 180:
            smooth_mouse_move(100, 0, duration=0.2, steps=20)
        else:
            smooth_mouse_move(-100, 0, duration=0.2, steps=20)


    while True:
        size_diff = c.size_diff
        log(c.ego_angle,size_diff)
        if size_diff and size_diff > 100:
            p('dd',0.1)
        elif size_diff and size_diff < -100:
            p('aa',0.1)
        if c.waits_limit(['F'],0.3):
            break
    pyautogui.keyUp('w')
    c.model_loop_end()
    # smooth_mouse_move(500000, 0, duration=t, steps=50)


def 登录(zh):
    wait_start = waits(['菜单','退出登录'])
    if wait_start == '菜单':
        pyautogui.press('esc')
        time.sleep(1.5)
        click('退出2')
        click('退出登录标识')
    click('退出登录')
    click('退出')
    click('登录其他账号')
    click('输入账号')
    text = zh.replace('\n','')
    keyboard.write(text, delay=0.01)
    click('输入密码')
    keyboard.write('zxc147123', delay=0.01)
    click('同意')
    click('进入游戏')
    click('点击进入')
    if waits(['菜单','空月祝福']) == '空月祝福':
        click('空月祝福')
        if waits(['空月祝福', '空白位置']) == '空月祝福':
            click('空月祝福')
        waits(['空白位置'],0.8)
        t = time.time()
        while True:
            click_limit('空白位置',0.5)
            if time.time() - t > 1:
                break
def 返回主界面():
    while not waits_limit(['菜单']):
        pyautogui.press('esc')
        time.sleep(0.5)

def 邮件领取():
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('esc')
    if waits(['邮件待领取','邮件'],0.95) == '邮件待领取':
        click('邮件待领取')
        click('全部领取')
        if waits(['空白位置','关闭']) == '空白位置':
            click('空白位置')
    返回主界面()

def 兑换码():
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('esc')
    if waits(['邮件待领取','邮件'],0.95):
        pyautogui.click(get_position([55, 1096]))
    waits(['关闭'])
    pyautogui.click(get_position([227, 753]))
    for code in codes:
        click('兑换码_前往兑换')
        click('兑换码_输入兑换码')
        keyboard.write(code, delay=0.01)
        waits(['兑换码_兑换'])
        time.sleep(0.3)
        click('兑换码_兑换')
        if c.waits(['兑换码_兑换码已被使用','兑换码_确认']) == '兑换码_兑换码已被使用':
            click('退出标识')
        else:
            click('兑换码_确认')
            click('退出标识')
    time.sleep(0.5)
    click('关闭')
    if waits(['邮件待领取','邮件'],0.95) == '邮件待领取':
        click('邮件待领取')
        click('全部领取')
        if waits(['空白位置','关闭']) == '空白位置':
            click('空白位置')
    返回主界面()

def 移动枫丹():
    waits(['菜单'])
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(get_position([62, 591]))
    pyautogui.click(get_position([63, 846]))
    click('地图标识')
    click(waits(['地图标识枫丹1','地图标识枫丹2']))
    pyautogui.click(get_position([1287, 716]))
    time.sleep(0.5)
    click_limit('传送点',1)
    time.sleep(0.5)
    click_limit('传送',1)

def 枫丹合成台():
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('1')
    pyautogui.keyDown('w')
    time.sleep(4)
    pyautogui.keyDown('d')
    time.sleep(0.6)
    pyautogui.keyUp('d')
    time.sleep(1)
    pyautogui.keyUp('w')
    log('移动到枫丹合成台')

def 枫丹凯瑟琳():
    waits(['菜单'])
    time.sleep(1)
    pyautogui.keyDown('w')
    time.sleep(1)
    pyautogui.keyDown('a')
    time.sleep(1.7)
    pyautogui.keyUp('a')
    time.sleep(0.3)
    pyautogui.keyUp('w')
    log('移动到枫丹凯瑟琳')

def 探索派遣():
    waits(['F'])
    pyautogui.press('f')
    time.sleep(1)
    pyautogui.press(' ')
    time.sleep(1)
    click('探索派遣')
    if waits(['全部领取标识','召回']) == '全部领取标识':
        click('全部领取标识')
        click('再次派遣标识')
    click('关闭')

def 历练点():
    waits(['菜单'])
    pyautogui.press('f1')
    click(waits(['委托标识1','委托标识2']))
    if waits(['历练点奖励','历练点奖励2']) == '历练点奖励':
        click('历练点奖励')
        click('空白位置')
    click(waits(['关闭2']))

def 每日委托():
    waits(['F'])
    pyautogui.press('f')
    time.sleep(1)
    pyautogui.press(' ')
    time.sleep(1)
    click('每日委托')
    time.sleep(1)
    pyautogui.press(' ')
    click_limit('空白位置',3)


def 合成():
    waits(['F'])
    pyautogui.press('f')
    time.sleep(1)
    pyautogui.press(' ')
    time.sleep(1)
    waits(['关闭'])
    if waits(['浓缩树脂','关闭']) == '浓缩树脂':
        click('合成')
        click('确认')
        click('关闭')
        return 1
    click('关闭')
    return 0

def 纪行():
    waits(['菜单'])
    pyautogui.press('f4')
    time.sleep(0.5)
    if waits(['纪行任务2','纪行任务1','菜单','关闭'],0.95) == '关闭':
        if waits(['纪行任务2', '纪行任务1', '菜单', '关闭'], 0.95) == '关闭':
            click(waits(['关闭']))
    waits_1 = waits(['纪行任务2','纪行任务1','菜单'],0.95)
    if waits_1 == '纪行任务2':
        click('纪行任务2')
        click('一键领取')
        time.sleep(0.5)
        pyautogui.press(' ')
        waits(['关闭'])
        click_limit('空白位置', 1)
        time.sleep(1)
        if waits(['珍珠纪行2','珍珠纪行1'],0.95) == '珍珠纪行2':
            click('珍珠纪行2')
            click('一键领取')
            click('空白位置')
        click(waits(['关闭']))
    elif waits_1 == '纪行任务1':
        click(waits(['关闭']))


def 圣遗物分解():
    waits(['菜单'])
    time.sleep(1.5)
    pyautogui.press('b')
    waits_1 = waits_many(['确认','背包_圣遗物1','背包_圣遗物2'])
    if '确认' in waits_1:
        click('确认')
        time.sleep(0.5)
    click(waits(['背包_圣遗物1','背包_圣遗物2']))
    click('分解')
    click('快速选择')
    click('确认选择')
    if waits(['分解2','分解3']) == '分解2':
        click('分解2')
        click('进行分解')
        click('空白位置')
    click('关闭')
    click('关闭')

def 秘境_圣遗物(zh_num,num):
    if num == 1:
        name = '圣遗物_虹灵的净土'
    elif num == 2:
        name = '圣遗物_褪色的剧场'
    elif num == 3:
        name = '圣遗物_罪祸的终末'
    elif num == 4:
        name = '圣遗物_岩中幽谷'
    elif num == 5:
        name = '圣遗物_荒废砌造坞'
    elif num == 6:
        name = '圣遗物_霜凝的机枢'
    else:
        name = None

    if zh_num == 0:
        fight_txt = '火茜希芙'
    elif zh_num == 1:
        fight_txt = '那维莱特'
    elif zh_num == 2:
        fight_txt = '散兵'
    elif zh_num == 3:
        fight_txt = '火艾'
    elif zh_num == 4:
        fight_txt = '火希娜班'
    elif zh_num == 5:
        fight_txt = '火希钟班'
    elif zh_num == 6:
        fight_txt = '仆人'
    elif zh_num == 7:
        fight_txt = '菲伊心爱'
    else:
        fight_txt = None

    waits(['菜单'])
    pyautogui.press('f1')
    click(waits(['秘境标识1','秘境标识2']))
    click(waits(['秘境圣遗物1', '秘境圣遗物2']))
    move('圣遗物传送标识')
    scroll_click(name, '圣遗物传送')
    click_limit('传送',2)
    time.sleep(2)
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.keyDown('w')
    time.sleep(0.4)
    pyautogui.rightClick()
    time.sleep(0.8)
    pyautogui.keyUp('w')
    副本战斗(fight_txt)
    # if waits(['须弥复活点','菜单']) == '须弥复活点':
    #     秘境_圣遗物(num)

def 晶蝶传送(name):
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('m')
    c.func_loop_start(lambda : pyautogui.press('f'))
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(get_position([62, 591]))
    pyautogui.click(get_position([63, 846]))
    if name == '晶蝶传送点3':
        pyautogui.click(get_position([63, 846]))
    click('地图标识')
    click(waits(['枫丹地图标识1','枫丹地图标识2']))
    click(name)
    time.sleep(0.4)
    click_limit('传送',1)

def 捕获晶蝶1():
    waits(['菜单'])
    time.sleep(0.3)
    pyautogui.keyDown('d')
    time.sleep(0.4)
    pyautogui.keyDown('shift')
    time.sleep(0.3)
    pyautogui.keyDown('ctrl')
    time.sleep(3)
    pyautogui.keyUp('ctrl')
    pyautogui.keyUp('shift')
    time.sleep(0.3)
    pyautogui.keyDown('s')
    pyautogui.keyUp('d')
    time.sleep(0.5)
    pyautogui.keyUp('s')

def 捕获晶蝶2():
    waits(['菜单'])
    time.sleep(0.3)
    pyautogui.keyDown('d')
    time.sleep(0.3)
    pyautogui.keyDown('shift')
    time.sleep(0.3)
    pyautogui.keyUp('shift')
    pyautogui.keyDown('s')
    pyautogui.keyUp('d')
    time.sleep(0.3)
    pyautogui.keyDown('a')
    pyautogui.keyUp('s')
    time.sleep(0.2)
    pyautogui.keyUp('a')

def 捕获晶蝶3():
    waits(['菜单'])
    time.sleep(0.6)
    pyautogui.keyDown('space')
    time.sleep(1.5)
    pyautogui.keyUp('space')

def 晶蝶():

    晶蝶传送('晶蝶传送点1')
    捕获晶蝶1()
    晶蝶传送('晶蝶传送点2')
    捕获晶蝶2()
    晶蝶传送('晶蝶传送点3')
    捕获晶蝶3()
    c.func_loop_end()

def 须弥回血传送():
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(get_position([62, 591]))
    pyautogui.click(get_position([63, 846]))
    pyautogui.click(get_position([63, 846]))
    click('地图标识')
    click(waits(['须弥地图标识1','须弥地图标识2']))
    pyautogui.click(get_position([1885, 1183]))
    # click('须弥传送点1')
    time.sleep(0.4)
    click_limit('传送',1)
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('1')
    time.sleep(2)

def 切换副本队伍():
    waits(['菜单'])
    pyautogui.press('l')
    click('队伍选择')
    if waits(['副本队伍标识1','副本队伍标识2']) == '副本队伍标识1':
        click('副本队伍标识1')
        click('确认')
        click('出战')
    else:
        pyautogui.press('esc')
    click(waits(['关闭']))

def 切换常用队伍():
    waits(['菜单'])
    pyautogui.press('l')
    click('队伍选择')
    if waits(['常用队伍标识1','常用队伍标识2']) == '常用队伍标识1':
        click('常用队伍标识1')
        click('确认')
        click('出战')
    else:
        pyautogui.press('esc')
    click(waits(['关闭']))


def p(s,t = 1.0):
    start_time = time.time()
    if s == 'A':
        while True:
            pyautogui.click()
            time.sleep(0.05)
            if time.time() - start_time >t:
                break
    elif s == 'AA':
        pyautogui.mouseDown()
        time.sleep(t)
        pyautogui.mouseUp()
    elif s == 'R':
        pyautogui.rightClick()
    elif s == 'S':
        time.sleep(t)
    elif s == 'AAA':
        time.sleep(0.1)
        pyautogui.mouseDown()
        smooth_mouse_move(500000, 0, duration=t, steps=50)
        pyautogui.mouseUp()
        time.sleep(0.1)
    elif type(s) == num:
        pyautogui.press(s)
    elif len(s)==1:
        while True:
            pyautogui.press(s)
            time.sleep(0.05)
            if time.time() - start_time >t:
                break
    elif len(s)==2:
        time.sleep(0.1)
        pyautogui.keyDown(s[0])
        time.sleep(t)
        pyautogui.keyUp(s[0])



def 副本战斗(fight_txt):
    n = 0
    while True:
        c.time_limit = 0.2
        res = waits(['副本标识','F'])
        if res == 'F':
            pyautogui.press('f')
            click('挑战')
            time.sleep(0.5)
            click('挑战')
            waits(['任意位置关闭'])
            time.sleep(0.5)
            click('任意位置关闭')
            pyautogui.keyDown('w')
            if waits_speed(['启动']):
                pyautogui.keyUp('w')
        c.wait_loop_start('挑战达成')
        pyautogui.press('f')
        while True:
            for s in AutoFight[fight_txt].split(' '):
                if c.wait_flag:
                    break
                if '(' in s:
                    key = s.split('(')[0]
                    t = s.split('(')[1].replace(')','')
                    p(key, float(t))
                else:
                    p(s)
            if c.wait_flag:
                pyautogui.press('3')
                break
        c.time_limit = 0.02
        time.sleep(3)
        get_ego_angle()
        pyautogui.press('f')
        time.sleep(1)
        pyautogui.moveTo([0,0])
        w1 = waits_many(['秘宝领取_原粹树脂','秘宝领取_浓缩树脂','秘宝领取_转换标识','秘宝领取_20原粹树脂'])
        if '秘宝领取_浓缩树脂' in w1:
            w_sz = waits(['浓缩树脂1', '浓缩树脂标识'])
            pyautogui.click(get_position(浓缩树脂使用坐标))
            log(n)
            if w_sz == '浓缩树脂1' and n >= 2:
                click('退出标识')
                return
        elif '秘宝领取_转换标识' in w1:
            if '秘宝领取_20原粹树脂' in w1:
                click('秘宝领取_转换')
                time.sleep(0.5)
            pyautogui.click(get_position(原粹树脂使用坐标))
            click('退出标识')
            return
        elif '秘宝领取_原粹树脂' in w1:
            pyautogui.press('esc')
            time.sleep(0.5)
            pyautogui.press('esc')
            click('确认标识')
            return

        click('挑战')
        waits(['任意位置关闭'])
        time.sleep(0.5)
        click('任意位置关闭')
        pyautogui.keyDown('w')
        if waits_speed(['启动']):
            pyautogui.keyUp('w')

        n += 1

def 移动幽境危战():
    waits(['菜单'])
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(6):
        pyautogui.click(get_position([63, 846]))
    click('地图标识')
    click(waits(['地图标识蒙德1','地图标识蒙德2']))
    pyautogui.click(get_position([925, 1394]))
    time.sleep(0.5)
    click_limit('传送',1)

def 幽境危战战斗(fight_txt):
    waits(['离开副本'])
    time.sleep(3)
    p('ww',0.2)
    pyautogui.rightClick()
    while True:
        focus = get_focus_window()
        if focus and '原神' not in focus:
            continue
        for s in AutoFight[fight_txt].split(' '):
            if waits_check_speed(['退出标识']):
                break
            if '(' in s:
                key = s.split('(')[0]
                t = s.split('(')[1].replace(')', '')
                p(key, float(t))
            else:
                p(s)
        if waits_check_speed(['退出标识']):
            pyautogui.press('3')
            break
    click('退出标识')

def 幽境危战战斗循环(zh_num,n):
    boss2 = [310,720]
    boss3 = [255, 960]
    if zh_num == 0:
        fight_txt = '火茜希芙_幽境危战'
    elif zh_num == 1:
        fight_txt = '丝爱芙夜_幽境危战'
    elif zh_num == 2:
        fight_txt = '散茜米莱_幽境危战'
    elif zh_num == 3:
        fight_txt = '火艾'
    elif zh_num == 4:
        fight_txt = '火希娜班_幽境危战'
    elif zh_num == 5:
        fight_txt = '火希钟班_幽境危战'
    elif zh_num == 6:
        fight_txt = '仆钟希班_幽境危战'
    elif zh_num == 7:
        fight_txt = '菲伊砂心_幽境危战'
    else:
        fight_txt = None
    waits(['菜单'])
    waits(['F'])
    time.sleep(1)
    pyautogui.press('f')
    dif_list = [f'幽境危战_{i}难度' for i in ['普通','进阶','困难','险恶','无畏']]
    if waits(dif_list) != '幽境危战_困难难度':
        time.sleep(0.5)
        click('幽境危战_难度下拉')
        click('幽境危战_困难难度选择')
    time.sleep(0.5)
    click('挑战')
    waits(['离开副本'])
    time.sleep(0.5)
    pyautogui.keyDown('w')
    if waits_speed(['F']):
        pyautogui.keyUp('w')
    pyautogui.press('f')
    waits(['挑战'])
    if n == 2:
        pyautogui.click(get_position(boss2))
    elif n == 3:
        pyautogui.click(get_position(boss3))
    click('挑战')
    while True:
        幽境危战战斗(fight_txt)
        if 幽境危战奖励领取():
            waits(['离开副本'])
            pyautogui.press('esc')
            click('退出登录标识')
            return


def 幽境危战奖励领取():
    waits(['离开副本'])
    pyautogui.press('s')
    time.sleep(0.2)
    pyautogui.middleClick()
    time.sleep(0.5)
    while True:
        position = c.check_one_pic('幽境危战_地脉奖励', num, c.processed_screen)
        print(position)
        focus = get_focus_window()
        if focus and '原神' not in focus:
            continue
        if not position:
            continue
        if waits_check_speed(['激活地脉之花']):
            break
        if position and 1480 > position[0][0] > 1080 and 800 > position[0][1] > 300:
            p('ww',0.5)
            continue
        if 450 > position[0][1] > 350:
            if position[0][0] > 1280:
                smooth_mouse_move(100, 0, duration=0.2, steps=20)
            else:
                smooth_mouse_move(-100, 0, duration=0.2, steps=20)
        else:
            if position[0][0] > 1280:
                smooth_mouse_move(100, 0, duration=0.2, steps=20)

            else:
                smooth_mouse_move(-100, 0, duration=0.2, steps=20)

    pyautogui.press('f')
    pyautogui.moveTo([0, 0])
    w1 = waits_many(['秘宝领取_原粹树脂', '秘宝领取_浓缩树脂', '秘宝领取_转换标识'])
    if '秘宝领取_浓缩树脂' in w1:
        w_sz = waits(['浓缩树脂1', '浓缩树脂标识'],0.95)
        log(w_sz)
        click('使用')
        if w_sz == '浓缩树脂1':
            click('退出标识')
            return True
        click('挑战')


def 每日(zh_num,n):
    登录(zh[zh_num])
    邮件领取()
    移动枫丹()
    枫丹合成台()
    res = 合成()
    if res:
        切换副本队伍()
        晶蝶()
        须弥回血传送()
        秘境_圣遗物(zh_num,n)
        圣遗物分解()
        切换常用队伍()
    移动枫丹()
    枫丹凯瑟琳()
    历练点()
    探索派遣()
    每日委托()
    纪行()

def 成就领取():
    while 1:
        click('成就领取')
        click('空白位置')

def 每日2(zh_num,n):
    登录(zh[zh_num])
    邮件领取()
    移动枫丹()
    枫丹合成台()
    res = 合成()
    if res:
        # 晶蝶()
        移动幽境危战()
        幽境危战战斗循环(zh_num,n)
        圣遗物分解()
    移动枫丹()
    枫丹凯瑟琳()
    历练点()
    探索派遣()
    每日委托()
    纪行()

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
if __name__ == '__main__':
    log('开始执行')
    # time.sleep(1)
    res = c.t_match.save_pic_loc('秘宝领取_20原粹树脂',json_path)
    c.check_start()
    秘境_圣遗物(7, 6)
    # 须弥回血传送()
    # # 幽境危战战斗循环(5, 3)
    # # 每日2(7,1)
    # # 成就领取()
    # 兑换码()
    # c.check_stop()
