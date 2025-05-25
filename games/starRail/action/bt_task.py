from games.starRail.action.bt_func import check,windows_title,control
from func.common import *

c = check(windows_title)

phone_position = (29, 57)

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
    c.wait_click('开始游戏')
    c.wait_click('点击进入')
    while True:
        if c.waits_limit(['Enter']):
            break
        c.send_key('w')


if __name__ == '__main__':
    # c.save_pic_loc('test',0.8)

    log('执行开始')
    c.check_start()

    # time.sleep(0.5)

    # c.send_key('esc')
    登录('suixin001002@163.com')


    c.check_stop()

