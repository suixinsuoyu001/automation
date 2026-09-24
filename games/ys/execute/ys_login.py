import time

from games.ys.action.ys_action import *



def logins():
    c.g_match.click(f'图标{resolution[0]}')
    # game_start(windows_title)
    c.check_start()
    # 屏蔽原神窗口的中文输入法，防止登录时切换成中文输入
    c.control.hwnd = get_hwnd(windows_title)
    c.control.disable_ime_all()
    # 启动输入法看门狗：仅在原神窗口处于前台时把输入法/输入语言切到英文，
    # 游戏一失焦(或任务结束)立刻把输入语言还给系统，所以游戏外照常打中文
    c.control.start_ime_watchdog()
    try:
        for zh in zhs:
            # if zh in [zhs[4],zhs[5]]:
            #     continue
            登录(zh)
            # 兑换码()
            # 每次登录前再次屏蔽输入法，避免被系统重新关联
            c.control.hwnd = get_hwnd(windows_title)
            c.control.disable_ime_all()
            log('等待按下0')
            keyboard.wait('0')
    finally:
        # 无论正常结束还是异常退出，都要收起看门狗并还原输入法状态，
        # 免得把用户的输入语言留在英文
        c.control.stop_ime_watchdog()
        c.check_stop()

def login_one(n):
    """登录指定账号。

    n 支持两种写法，方便 GUI 直接传账号名，避免「序号和账号列表对不上」：
      * int 序号 -> 取 zh[n]（脚本里 `login_one(5)` 的老用法）
      * str      -> 直接当作账号本身（如 'xxx@126.com'）

    zh 来自 ys_action.py 的账号表。
    """
    if isinstance(n, int):
        account = zh[n]
    elif isinstance(n, str) and n.strip():
        account = n
    else:
        log(f'login_one: 无效的账号参数 {n!r}')
        return
    # game_start(windows_title)
    c.check_start()
    # 屏蔽原神窗口的中文输入法，防止登录时切换成中文输入
    c.control.hwnd = get_hwnd(windows_title)
    c.control.disable_ime_all()
    # 启动输入法看门狗：仅在原神窗口处于前台时强制英文输入
    c.control.start_ime_watchdog()
    try:
        登录(account)
    finally:
        c.control.stop_ime_watchdog()
        c.check_stop()      # 无论登录成功失败都收掉共享截图线程

zhs = [
        'kechengzhuang524@126.com',     #0
        'kemeihao694350@126.com',       #1
        # 'kenc40sklx6093@126.com',       #2
        # 'suixin001005@163.com',         #3
        # 'suixin001002@163.com',         #4
        # 'kengfeiyan34534@126.com',      #5
        'k6597975255692@sohu.com',      #6
        # '13280859317'                   #7
       ]


if __name__ == '__main__':

    # logins()
    login_one(6)
