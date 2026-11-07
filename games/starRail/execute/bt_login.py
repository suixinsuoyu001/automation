from games.starRail.action.bt_task import *
import keyboard


def _账号(n):
    """把 GUI 传来的参数换成账号字符串。

    n 支持三种写法（和原神 ys_login.login_one 一致）：
      * 就是 zhs 里的账号（含 ``13280859317`` 这种纯数字手机号）-> 原样使用；
      * int / 数字字符串 -> zhs 里对应编号的账号；
      * 其它非空字符串 -> 直接当作账号本身（账号页新加的账号也认）。
    返回 None 表示参数无效。
    """
    if isinstance(n, str):
        n = n.strip()
        if not n:
            return None
        # 先按账号名匹配：手机号账号也是纯数字，不能先当成序号
        if n in zhs:
            return n
        if n.isdigit():
            index = int(n)
            if 0 <= index < len(zhs):
                return zhs[index]
        return n
    try:
        index = int(n)
    except (TypeError, ValueError):
        return None
    return zhs[index] if 0 <= index < len(zhs) else None


def login_one(n):
    """登录指定账号（GUI：崩铁 -> 崩铁单账号登录）。

    输入法处理和原神 ys_login.login_one 完全一致：

        focus_or_start_game -> check_start -> disable_ime_all
            -> start_ime_watchdog -> 登录(账号)
            -> stop_ime_watchdog -> check_stop

    崩铁登录界面是 webview，点输入框会把中文输入法重新挂回来，只靠
    disable_ime_all 挡不住；start_ime_watchdog 会在游戏处于前台期间持续
    把输入法/输入语言切到英文，登录结束（或游戏失焦）立刻还原，
    所以游戏外照常打中文。
    """
    account = _账号(n)
    if not account:
        log(f'login_one: 无效的账号参数 {n!r}')
        return
    c.zhs = zhs
    # 窗口已经在 -> 只置前；不在 -> 点一次桌面图标启动
    c.focus_or_start_game()
    c.check_start()
    # 屏蔽崩铁窗口的中文输入法，防止登录时切换成中文输入
    c.control.hwnd = get_hwnd(windows_title)
    c.control.disable_ime_all()
    # 启动输入法看门狗：仅在崩铁窗口处于前台时强制英文输入，
    # 切出游戏后不影响其他程序正常输入中文
    c.control.start_ime_watchdog()
    try:
        登录(account)
    finally:
        # 无论登录成功失败，都要收起看门狗并还原输入法状态，
        # 免得把用户的输入语言留在英文
        c.control.stop_ime_watchdog()
        c.check_stop()      # 收掉共享截图线程


def logins():
    c.zhs = zhs
    # 窗口已经在 -> 只置前；不在 -> 点一次桌面图标启动
    c.focus_or_start_game()
    c.check_start()
    # 屏蔽游戏窗口的中文输入法，防止登录时切换成中文输入
    c.control.hwnd = get_hwnd(windows_title)
    c.control.disable_ime_all()
    # 启动输入法看门狗：仅在游戏窗口处于前台时强制英文输入，
    # 切出游戏后不影响其他程序正常输入中文
    c.control.start_ime_watchdog()
    try:
        for zh in c.zhs:
            登录(zh)
            # 邮件领取()
            # 巡星之礼领取()
            兑换码()
            if c.is_focus():
                c.control.activate()
            # 每次登录前再次屏蔽输入法，避免被系统重新关联
            c.control.hwnd = get_hwnd(windows_title)
            c.control.disable_ime_all()
            log('等待按下0')
            keyboard.wait('0')
    finally:
        c.control.stop_ime_watchdog()
        c.check_stop()

zhs = [
    'suixin001007@163.com', #0	流萤
    'suixin001006@163.com', #1	阿格莱雅
    'suixin001001@163.com', #2	大黑塔
    '13280859317',          #3	黄泉
    'suixin001002@163.com', #4 	遐蝶
    'suixin001005@163.com', #5 	万敌
    'suixin001008@163.com', #6	风堇
    'suixin001009@163.com', #7	希儿
    'suixin001003@163.com', #8	龙丹
    'suixin001004@163.com', #9	暂无
]

if __name__ == '__main__':
    # logins()
    login_one(8)

