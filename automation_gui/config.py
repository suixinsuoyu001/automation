"""全局配置：账号列表、任务定义、窗口尺寸等。

风格参考 ok-ww，所有可配置项集中在此，方便维护。
"""
import os

# 项目根目录（automation 仓库根）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本工具目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 账号配置文件
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

# 窗口尺寸（参考 ok-ww）
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

# 应用信息
APP_NAME = "Automation"
APP_TITLE = "自动化助手"
APP_VERSION = "v1.0.0"

# 任务页默认展示哪个游戏的任务
DEFAULT_GAME = "原神"

# 默认账号列表（原神）
DEFAULT_YS_ACCOUNTS = [
    "kechengzhuang524@126.com",   # 0
    "kemeihao694350@126.com",     # 1
    "kenc40sklx6093@126.com",     # 2
    "suixin001005@163.com",       # 3
    "suixin001002@163.com",       # 4
    "kengfeiyan34534@126.com",    # 5
    "k6597975255692@sohu.com",    # 6
    "13280859317",                # 7
]

# 默认账号列表（崩坏：星穹铁道）
DEFAULT_BT_ACCOUNTS = [
    "suixin001007@163.com",  # 0 流萤
    "suixin001006@163.com",  # 1 阿格莱雅
    "suixin001009@163.com",  # 2 希儿
    "suixin001001@163.com",  # 3 大黑塔
    "13280859317",           # 4 黄泉
    "suixin001002@163.com",  # 5 遐蝶
    "suixin001005@163.com",  # 6 万敌
    "suixin001003@163.com",  # 7 龙丹
    "suixin001004@163.com",  # 8 暂无
    "suixin001008@163.com",  # 9 风堇
]

# 原神圣遗物秘境：默认「编号 -> 模板图片名」映射。
# 首次运行会写入 games/ys/data/秘境圣遗物.json，之后以该 json 为准，
# 可在 GUI 的「秘境配置」页编辑（游戏脚本读取的是那份 json）。
YS_DOMAIN_NAMES = {
    1: "圣遗物_虹灵的净土",
    2: "圣遗物_褪色的剧场",
    3: "圣遗物_罪祸的终末",
    4: "圣遗物_岩中幽谷",
    5: "圣遗物_荒废砌造坞",
    6: "圣遗物_霜凝的机枢",
    7: "圣遗物_月童的库藏",
    8: "圣遗物_山风的荆冕",
}

# 原神队伍编号 -> 名称
YS_TEAM_NAMES = {
    0: "火茜希芙",
    1: "丝爱心塔",
    2: "散兵",
    3: "火艾",
    4: "火希娜班",
    5: "火希钟班",
    6: "仆人",
    7: "菲伊心爱",
}
