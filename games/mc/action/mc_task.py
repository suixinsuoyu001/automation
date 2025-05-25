import pyautogui
from func.common import *
from func.check import *
import ctypes
import time
from func.control.mc_control import *
from func.control.global_match import match


image_path = 'games/mc/image/'
json_path = 'games/mc/data/img_loc.json'

control = Control()
g_match = match(image_path,0.9)



c = check('鸣潮  ',image_path,json_path)


def pic_click(names,matches):
    for i in names:
        if i in matches:
            control.click(matches[i][0])
            return

# def pic_press(names,matches,s):
#     for i in names:
#         if i in matches:
#             pyautogui.press(s)
#             return

def loc_jl():
    print('loc_jl:开始朝奖励位置移动')
    def left_top():
        control.send_key_down('w')
        control.send_key_down('a')
        time.sleep(0.2)
        control.send_key_up('w')
        control.send_key_up('a')
        control.click_mid()
        time.sleep(0.2)
    def right_top():
        control.send_key_down('w')
        control.send_key_down('d')
        time.sleep(0.2)
        control.send_key_up('w')
        control.send_key_up('d')
        control.click_mid()
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
            control.send_key('w',0.5)
        time.sleep(0.2)
    print('loc_jl:已移动至奖励位置')


def mr(flag = 1):
    c.wait_click_limit('点击连接',2)
    wait = c.waits(['月卡标识','聊天标识'])
    time.sleep(0.5)
    wait = c.waits(['月卡标识', '聊天标识'])
    if wait == '月卡标识':
        c.wait_click('月卡标识')
        c.wait_click('空白位置')
    if flag == 1:
        讨伐强敌()
        战歌重奏()
    c.wait_press('聊天标识','f2')
    c.wait('关闭菜单2')
    c.click_point_until([100, 593],'周期挑战标识',0.8) #点击周期挑战
    c.scroll_click('长刃2','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    c.run_until('F','w',0.8)
    c.wait_press('F','f',0.8)
    c.wait_click('单人挑战')
    while 1:
        c.click_loop_until(['开启挑战'], ['聊天标识'], 0.95)
        time.sleep(0.5)
        c.run_until('F', 'w',0.8)
        c.wait_press('F', 'f', 0.8)
        control.send_key('shift')
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

def test():
    c.scroll_click('长刃2','前往')

def 战歌重奏():
    c.wait_press('聊天标识', 'f2')
    c.click_point_until([100, 593], '周期挑战标识') #点击周期挑战
    c.wait_click('战歌重奏')
    c.scroll_click('乌龟','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    control.send_key_down('w')
    time.sleep(0.5)
    control.click_right()
    time.sleep(4)
    control.send_key_up('w')
    c.waits(['F','领取奖励'], 0.8)

def 讨伐强敌():
    c.wait_press('聊天标识', 'f2')
    c.click_point_until([100, 593], '周期挑战标识') #点击周期挑战
    c.wait_click('讨伐强敌')
    c.scroll_click('辉萤军势','前往')
    c.wait_click('快速旅行')
    c.wait('聊天标识')
    control.send_key_down('w')
    time.sleep(0.5)
    control.click_right()
    time.sleep(4)
    control.send_key_up('w')
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
                control.click(v[0])
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
    click_names = ['跳过剧情2','快速旅行']
    esc_names = ['跳过剧情']
    names = []
    while True:
        matches = c.check_pic(click_names + esc_names + names, 0.8)
        print(matches)
        for i,v in matches.items():
            if i in click_names:
                control.click(v[0])
            if i in esc_names:
                c.wait_press(i, 'esc')

        time.sleep(0.2)

if __name__ == '__main__':
    c.t_match.save_pic_loc('聊天标识', json_path, 0.8)
    剧情()