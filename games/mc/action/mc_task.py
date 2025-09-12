import pyautogui
import pyperclip

from func.common import *
from func.check import *
import ctypes
import time
from func.control.global_match import match
from games.mc.data.mc_data import *



g_match = match(image_path,0.9)


c = check(windows_title,image_path,json_path)


def pic_click(names,matches):
    for i in names:
        if i in matches:
            c.control.click(matches[i][0])
            return

# def pic_press(names,matches,s):
#     for i in names:
#         if i in matches:
#             pyautogui.press(s)
#             return

def loc_jl():
    print('loc_jl:开始朝奖励位置移动')
    def left_top():
        c.control.send_key_down('w')
        c.control.send_key_down('a')
        time.sleep(0.2)
        c.control.send_key_up('w')
        c.control.send_key_up('a')
        c.control.click_mid()
        time.sleep(0.2)
    def right_top():
        c.control.send_key_down('w')
        c.control.send_key_down('d')
        time.sleep(0.2)
        c.control.send_key_up('w')
        c.control.send_key_up('d')
        c.control.click_mid()
        time.sleep(0.2)
    while 1:
        item_point = [1257, 694]
        match = c.match_one_pic('领取奖励',0.8)
        if not match:
            break
        point = match[0]
        dis_x = point[0]-item_point[0]
        dis_y = point[1]-item_point[1]
        if dis_x > 700 or abs(dis_y) > 200:
            right_top()
        elif dis_x < -700:
            left_top()
        else:
            c.control.send_key('w',0.5)
        time.sleep(0.2)
    print('loc_jl:已移动至奖励位置')


def 每日资源(凝素领域 = None,无音清剿 = None):
    # param1 凝素领域 佩枪2*3 重复3次 不填*直到体力打空
    # param2 无音清剿 哀恸谷*3 重复3次 不填*直到体力打空

    n = 0
    if 凝素领域:
        name1 = 凝素领域.split('*')[0]
        times1 = int(凝素领域.split('*')[1]) if len(凝素领域.split('*')) == 2 else None
        凝素领域战斗(name1,times1)
    if 无音清剿:
        name2 = 无音清剿.split('*')[0]
        times2 = int(无音清剿.split('*')[1]) if len(无音清剿.split('*')) == 2 else None
        res = 无音清剿战斗(name2,times2)
        n += res
    log(n)
    if n == 0:
        讨伐强敌()
        战歌重奏()
    传送到安全区域()


def 传送到安全区域():
    切换地图坐标 = [2132, 1338]
    黎那汐塔地图坐标 = [1564, 228]
    传送点坐标 = [828, 623]
    c.wait_press('Tab', 'm')
    time.sleep(0.5)
    c.control.click(切换地图坐标)
    time.sleep(0.8)
    c.control.click(黎那汐塔地图坐标)
    time.sleep(1)
    c.control.click(传送点坐标)
    c.wait_click('快速旅行')


def 凝素领域战斗(name = '长刃2',num_limit = None):
    num = 0
    c.wait_press('聊天标识','f2')
    c.wait('关闭菜单2')
    # 106, 408
    c.click_point_until([100, 408],'周期挑战标识',0.8) #点击周期挑战
    c.scroll_click(f'凝素领域_{name}','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    c.run_until('F','w',0.8)
    c.wait_press('F','f',0.8)
    c.wait_click('单人挑战')
    while 1:
        num += 1
        c.click_loop_until(['开启挑战'], ['聊天标识'], 0.95)
        print(num)
        if num-1 == num_limit:
            c.wait_press('聊天标识', 'esc')
            c.wait_click('确认')
            return num-1
        time.sleep(0.5)
        c.run_until('F', 'w',0.8)
        c.wait_press('F', 'f', 0.8)
        c.control.send_key('shift')
        time.sleep(5)
        c.waits(['F', '领取奖励'], 0.8)
        time.sleep(2)
        wait_res = c.waits(['F', '领取奖励'], 0.8)
        if wait_res == 'F':
            c.wait_press('F', 'f', 0.8)
        elif wait_res == '领取奖励':
            loc_jl()
            c.wait_press('F', 'f', 0.8)
        wait_res = c.waits(['确认', '80'], 0.95)
        if wait_res == '确认':
            c.wait_click('确认')
            c.wait_click('重新挑战')
        elif wait_res == '80':
            c.wait_click('80')
            wait_80 = c.waits(['重新挑战', '补充结晶波片'], 0.95)
            if wait_80 == '重新挑战':
                c.wait_click('重新挑战')
                wait_ts = c.waits(['提示', '聊天标识'], 0.95)
                if wait_ts == '提示':
                    c.wait_click('取消')
                    break
            elif wait_80 == '补充结晶波片':
                c.wait_click('取消')
                c.wait_click('40')
                break
        elif wait_res == '提示':
            c.wait_click('取消')
            break

    c.wait_click('退出副本')
    return num

def 奖励领取():
    res = 1 # 1刚使用完120体力 2刚使用完60体力 3体力耗尽
    c.wait_click('双倍领取')
    wait_1 = c.waits(['确定','补充结晶波片'])
    if wait_1 == '确定':
        c.wait_click('确定')
    elif wait_1 == '补充结晶波片':
        c.wait_click('取消')
        c.wait_click('单倍领取')
        wait_2 = c.waits(['确定', '补充结晶波片'])
        res = 2
        if wait_2 == '确定':
            c.wait_click('确定')
        elif wait_2 == '补充结晶波片':
            res = 3
            c.wait_click('取消')
            c.wait_press('单倍领取', 'esc')
    c.waits(['聊天标识'])
    return res


def 无音清剿战斗(name,num_limit = None):
    num = 0
    while 1:
        c.wait_press('聊天标识', 'f2')
        c.wait('关闭菜单2')
        c.click_point_until([100, 408], '周期挑战标识', 0.8)  # 点击周期挑战
        time.sleep(0.5)
        c.click(c.waits(['无音清剿标识1', '无音清剿标识2']))
        c.scroll_click(f'无音清剿_{name}', '前往')
        c.wait_click('快速旅行')
        c.wait('聊天标识')
        c.run(4)
        c.waits(['F', '领取奖励'], 0.8)
        time.sleep(2)
        wait_res = c.waits(['F', '领取奖励'], 0.8)
        if wait_res == 'F':
            c.wait_press('F', 'f', 0.8)
        elif wait_res == '领取奖励':
            loc_jl()
            c.wait_press('F', 'f', 0.8)
        res = 奖励领取()
        if res != 3:
            num += 1
        if num == num_limit or res != 1:
            return num


def 战歌重奏():
    c.wait_press('聊天标识', 'f2')
    c.click_point_until([100, 410], '周期挑战标识') #点击周期挑战
    c.wait_click('战歌重奏')
    c.scroll_click('乌龟','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    c.control.send_key_down('w')
    time.sleep(0.5)
    c.control.click_right()
    time.sleep(4)
    c.control.send_key_up('w')
    c.waits(['F','领取奖励'], 0.8)

def 讨伐强敌():
    c.wait_press('聊天标识', 'f2')
    c.click_point_until([100, 410], '周期挑战标识') #点击周期挑战
    c.wait_click('讨伐强敌')
    c.scroll_click('辉萤军势','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    c.control.send_key_down('w')
    time.sleep(0.5)
    c.control.click_right()
    time.sleep(4)
    c.control.send_key_up('w')
    c.waits(['F','领取奖励'], 0.8)

def 每日奖励():
    c.wait_press('聊天标识', 'f2')
    c.click_point_until([100, 230], '活跃度标识')  #点击活跃度奖励
    time.sleep(0.5)
    c.click_loop_until(['领取'],['满活跃','满活跃_已领取'],0.95)
    c.wait_click_limit('满活跃',1)
    c.wait_click_limit('空白位置',1)
    c.wait_press('关闭菜单2','esc')

def 先约电台():
    c.wait_press('聊天标识', 'f4')
    wait = c.waits(['提示','电台任务'])
    if wait == '提示':
        c.wait_click('确认')
        return
    c.wait_click_limit('电台任务',2)
    c.wait_click_limit('一键领取',1) 
    c.wait_click_limit('电台奖励', 2)
    c.wait_click_limit('一键领取', 1)
    c.wait_click_limit('确定', 1)
    c.wait_click_limit('空白位置', 1)
    c.wait_click('关闭电台')

def change_zh():
    c.wait_press('聊天标识', 'esc')
    c.wait_click('注销')
    c.wait_click('返回登录')



def 活动():
    c.check_start()
    click_names = ['骰子','点击继续','关闭']
    click_names = ['活动/'+i for i in click_names]
    esc_names = ['空白位置']
    esc_names = ['活动/' + i for i in esc_names]
    names = []
    names = ['活动/' + i for i in names]
    while True:
        matches = c.check_pic(click_names + esc_names + names, 0.8)
        print(matches)
        for i,v in matches.items():
            if i in click_names:
                c.control.click(v[0])
            if i in esc_names:
                c.wait_press(i, 'esc')

        time.sleep(0.2)

def 切换账号(n):
    g_match.click('账号下拉')
    time.sleep(0.5)
    g_match.click_num('账号标识',3)
    g_match.click('登录')

def 剧情():
    c.check_start()
    click_names = ['跳过剧情2','快速旅行','提示翻页']
    esc_names = ['跳过剧情','提示关闭']
    names = []
    while True:
        matches = c.check_pic(click_names + esc_names + names, 0.9)
        print(matches)
        for i,v in matches.items():
            if i in click_names:
                c.control.click(v[0])
            if i in esc_names:
                c.wait_press(i, 'esc')

        time.sleep(0.1)

def 根据特征码获取账号信息():
    c.wait_press('Tab', 'esc')
    time.sleep(0.5)
    c.click('复制特征码')
    tzm = pyperclip.paste()
    return id_mapping[tzm]

def 登录账号(n = 1):
    game_start(windows_title)
    login_match = g_match.waits(['点击连接', '登录', 'Tab'])
    if login_match in ['Tab']:
        id_num = 根据特征码获取账号信息()
        if id_num != n:
            c.wait_click('注销')
            c.wait_click('返回登录')
        else:
            c.wait_press('注销', 'esc')
            return
    elif login_match == '点击连接':
        g_match.click('注销账号')
        g_match.click('确认登出')
        g_match.click('登入')
    zh_match = g_match.waits(['账号1_已登录', '账号2_已登录', '账号3_已登录'],0.95)
    if zh_match == f'账号{n}_已登录':
        g_match.click('登录')
    else:
        g_match.click('账号下拉')
        time.sleep(0.5)
        g_match.click(f'账号{n}_待选择')
        g_match.click('登录')
    while c.waits(['月卡标识','聊天标识','点击连接']) == '点击连接':
        c.wait_click_limit('点击连接',2,0.8)
        time.sleep(2)
    c.waits(['月卡标识','聊天标识'])
    time.sleep(0.5)
    wait = c.waits(['月卡标识', '聊天标识'])
    if wait == '月卡标识':
        c.wait_click('月卡标识')
        c.wait_click('空白位置')

def 每日(n,凝素领域 = None,无音清剿 = None):
    登录账号(n)
    每日资源(凝素领域, 无音清剿)
    每日奖励()
    先约电台()



if __name__ == '__main__':
    c.t_match.save_pic_loc('Tab', json_path, 0.8)
    #
    #
    # 剧情()
    # 无音清剿(name='哀恸谷')
    # 凝素领域('佩枪2',3)
    # 每日(3,param1='佩枪2*3',param2='哀恸谷')


    c.check_stop()