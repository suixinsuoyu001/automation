import time

from games.ys.action.ys_action import *

# 1 纳塔套
# 2 生命之契燃烧套
# 3 枫丹套
# 4 层岩套
# 5 下落套
# 6 挪德卡莱套

# 账号表统一由 games/ys/data/账号.json 提供
# （ys_action 里已定义 zh / zhs / 获取账号），所以这里不再写死。

def run():
    # 打开betterGi2()
    c.g_match.click(f'图标{resolution[0]}')
    # game_start(windows_title)
    c.check_start()
    每日(0, 7)
    每日(1, 5)
    # 每日(2, 6)
    # 每日(3, 5)
    # 每日(4, 1)
    # 每日(5, 1)
    每日(6, 8)
    # 每日(7, 6)
    c.check_stop()

def run2():
    game_start(windows_title)
    c.check_start()
    每日2(0,3)
    每日2(1,3)
    每日2(2,3)
    每日2(3,3)
    每日2(4,3)
    每日2(5,3)
    每日2(6,3)
    每日2(7,3)
    c.check_stop()

def run3(zh_num = 0, num = 1):
    """只刷圣遗物秘境（GUI 任务「原神圣遗物秘境」走这个入口）。

    zh_num: 账号/队伍编号（决定用哪套输出轴 fight_txt，见 秘境_圣遗物）
    num:    秘境编号（对应 games/ys/data/秘境圣遗物.json）

    流程：切换副本队伍 -> 进秘境战斗领奖 -> 分解圣遗物 -> 切回常用队伍

    注意：`秘境_圣遗物` 是**动作层**函数，只负责「传送 -> 战斗 -> 领奖」，
    既不会启动截图循环、也不负责登录。所以这里必须自己 check_start/check_stop，
    否则 processed_screen 一直是 None，里面的 waits 会一直空等。

    前提：游戏已启动，并且已经登录到 zh_num 对应的账号。
    """
    game_start(windows_title)
    c.check_start()
    try:
        切换副本队伍()
        try:
            秘境_圣遗物(zh_num, num)
            圣遗物分解()
        finally:
            # 不管打没打完都切回常用队伍，避免账号卡在副本队伍上。
            # 这里吞掉异常：否则 finally 里抛的错会盖掉真正失败的原因。
            try:
                切换常用队伍()
            except Exception as e:
                log(f'run3: 切回常用队伍失败: {e}')
    finally:
        c.check_stop()      # 无论成功失败都收掉共享截图线程

if __name__ == '__main__':

    # # 登录(zh[0])
    # 邮件领取()
    # # 每日(0,1)
    run()
    # run2()
    # c.check_start()
    # 每日2(1, 3)
    # click(waits(['枫丹地图标识1', '枫丹地图标识2']))