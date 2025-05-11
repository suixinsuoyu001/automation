import time

from func.common import *
from func.check import *
from func.control.global_match import *
import pyautogui
import keyboard

pyautogui.FAILSAFE = False  # 禁用 fail-safe

image_path = 'games/ys/image/'
json_path = 'games/ys/data/img_loc.json'

c = check('原神',image_path,json_path)
m = match(image_path,0.9)

num = 0.9

def click(name, num=num):
    if c.processed_screen is None:
        print('check_start未运行')
        return
    print(f'click:{name} 开始捕获')
    while True:
        focus = get_focus_window()
        position = c.check_one_pic(name, num, c.processed_screen)
        if focus and '原神' in focus and position:
            pyautogui.click(position[0])
            time.sleep(0.4)
            break
        time.sleep(0.02)
    print(f'click:{name} 已捕获并点击')

def move(name, num=num):
    if c.processed_screen is None:
        print('check_start未运行')
        return
    print(f'click:{name} 开始捕获')
    while True:
        focus = get_focus_window()
        position = c.check_one_pic(name, num, c.processed_screen)
        if focus and '原神' in focus and position:
            pyautogui.moveTo(position[1])
            time.sleep(0.4)
            break
        time.sleep(0.02)
    print(f'click:{name} 已捕获并点击')

def click_limit(name,t,num = 0.9):
    if c.processed_screen is None:
        print('check_start未运行')
        return
    print(f'click_limit:{name} 开始捕获')
    start_time = time.time()
    while True:
        control.activate()
        position = c.check_one_pic(name, num, c.processed_screen)
        if position is not None:
            pyautogui.click(position[0])
            time.sleep(0.4)
            print(f'click_limit:{name} 已捕获并点击')
            break
        time.sleep(0.02)
        if time.time() - start_time > t:
            print(f'click_limit:{name} 未捕获，超时取消')
            break

def waits(names,num = num):
    print(f'waits:{names} 开始捕获')
    if c.processed_screen is None:
        print('check_start未运行')
        return
    while True:
        focus = get_focus_window()
        if not (focus and '原神' in focus):
            continue
        for name in names:
            position = c.check_one_pic(name,num,c.processed_screen)
            if position:
                print(f'wait: {name} 已找到')
                time.sleep(0.2)
                return name

def scroll_click(name1,name2,num = num):
    while 1:
        match = c.match_one_pic(name1, num)
        if match:
            print(f'scroll_click:已识别{name1}')
            break
        for i in range(8):
            pyautogui.scroll(-5)
        time.sleep(0.5)
    matches = c.match_pics(name2,num)
    print(match)
    print(matches)
    for i in matches:

        if match[1][1]<i['y']+100:
            pyautogui.click([i['x'],i['y']])
            break

    print(f'scroll_click:已识别{name2}并点击')

def 打开betterGi():
    m.click('betterGi')
    if m.waits(['脚本_启动','脚本_停止']) == '脚本_启动':
        m.click('脚本_启动')
    else:
        m.click('原神图标')


def 登录(zh):
    wait_start = waits(['菜单','退出登录'])
    if wait_start == '菜单':
        pyautogui.press('esc')
        time.sleep(0.8)
        click('退出2')
        click('退出至登录界面')
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
        time.sleep(0.5)
        pyautogui.press(' ')

def 移动枫丹():
    waits(['菜单'])
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(62, 591)
    pyautogui.click(63, 846)
    click('地图标识')
    click(waits(['枫丹地图标识1','枫丹地图标识2']))
    pyautogui.click(1287, 716)
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
    print('移动到枫丹合成台')

def 枫丹凯瑟琳():
    waits(['菜单'])
    time.sleep(1)
    pyautogui.keyDown('w')
    time.sleep(1)
    pyautogui.keyDown('a')
    time.sleep(2)
    pyautogui.keyUp('a')
    time.sleep(0.7)
    pyautogui.keyUp('w')
    print('移动到枫丹凯瑟琳')

def 探索派遣():
    waits(['F'])
    pyautogui.press('f')
    time.sleep(1)
    pyautogui.press(' ')
    time.sleep(1)
    click('探索派遣')
    if waits(['全部领取','召回']) == '全部领取':
        click('全部领取')
        click('再次派遣')
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
    waits(['关闭'])
    if waits(['纪行任务2','纪行任务1'],0.95) == '纪行任务2':
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

def 圣遗物分解():
    waits(['菜单'])
    pyautogui.press('b')
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

def 秘境_圣遗物(num):
    if num == 1:
        name = '圣遗物_虹灵的净土'
    elif num == 2:
        name = '圣遗物_罪祸的终末'
    elif num == 3:
        name = '圣遗物_岩中幽谷'
    else:
        name = None

    waits(['菜单'])
    pyautogui.press('f1')
    click(waits(['秘境标识1','秘境标识2']))
    click(waits(['秘境圣遗物1', '秘境圣遗物2']))
    move('圣遗物传送标识')
    scroll_click(name, '圣遗物传送')
    click_limit('传送',2)
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.keyDown('w')
    time.sleep(0.4)
    pyautogui.rightClick()
    time.sleep(0.8)
    pyautogui.keyUp('w')
    pyautogui.press('i')
    waits(['单人挑战'])
    waits(['菜单'])
    if waits(['须弥复活点','菜单']) == '须弥复活点':
        秘境_圣遗物(num)

def 晶蝶传送(name):
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(62, 591)
    pyautogui.click(63, 846)
    if name == '晶蝶传送点3':
        pyautogui.click(63, 846)
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

def 须弥回血传送():
    waits(['菜单'])
    time.sleep(0.5)
    pyautogui.press('m')
    waits(['关闭'])
    for i in range(5):
        pyautogui.click(62, 591)
    pyautogui.click(63, 846)
    pyautogui.click(63, 846)
    click('地图标识')
    click(waits(['须弥地图标识1','须弥地图标识2']))
    click('须弥传送点1')
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

def 每日(n):
    移动枫丹()
    枫丹合成台()
    res = 合成()
    if res:
        切换副本队伍()
        晶蝶()
        须弥回血传送()
        秘境_圣遗物(n)
        切换常用队伍()
    移动枫丹()
    枫丹凯瑟琳()
    历练点()
    探索派遣()
    每日委托()
    纪行()

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
    res = c.t_match.save_pic_loc('须弥地图标识1',json_path)
    # print(res)
    # m.click('原神图标')wd
    # # m.wait('退出登录')
    # c.check_start()
    #m
    # # 登录(zh[2])
    # 每日(1)
    # # 圣遗物分解()
    # c.check_stop()


