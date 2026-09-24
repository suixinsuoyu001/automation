"""原神队伍配置存储：读写 games/ys/data/队伍.json。

这份映射表同时被游戏脚本 `games/ys/action/ys_action.py` 读取
（见其中的 `队伍json` / `获取队伍配置`），所以在这里改完，
任务执行时用的就是新配置，不需要动代码。

每个编号（= 账号序号）一条记录：

    {"名称": "火茜希芙",              # 显示用：账号下拉框里显示成「账号（名称）」
     "秘境": "火茜希芙",              # 圣遗物秘境的输出轴名
     "幽境危战": "火茜希芙_幽境危战"}  # 幽境危战的输出轴名

**注意**：`秘境` / `幽境危战` 的值必须是 `games/ys/data/AutoFight.json` 里
真实存在的 key，写错了战斗时取不到输出轴（`AutoFight[key]` 会 KeyError）。
"""
import json
import os

from automation_gui import config

# 与 games/ys/action/ys_action.py 里的 队伍json 保持一致
TEAM_FILE = os.path.join(config.ROOT_DIR, "games", "ys", "data", "队伍.json")

# 每条记录的字段
FIELDS = ("名称", "秘境", "幽境危战")

# 场景 -> 字段名（游戏脚本按场景取输出轴）
SCENE_FIELD = {
    "秘境": "秘境",
    "幽境危战": "幽境危战",
}


def default_teams():
    """默认映射（来自 config.YS_TEAMS），键统一转成字符串。"""
    return {str(index): dict(item)
            for index, item in sorted(config.YS_TEAMS.items())}


def load_teams():
    """读取映射表，返回 {'0': {'名称': ..., '秘境': ..., '幽境危战': ...}, ...}。

    文件不存在时用默认映射创建，保证游戏脚本一定读得到。
    """
    if not os.path.exists(TEAM_FILE):
        data = default_teams()
        save_teams(data)
        return data
    try:
        with open(TEAM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default_teams()
        return data
    except Exception:
        return default_teams()


def save_teams(data):
    """写回映射表（中文不转义、缩进 2，与 秘境圣遗物.json 风格一致）。"""
    os.makedirs(os.path.dirname(TEAM_FILE), exist_ok=True)
    with open(TEAM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def team_name(index):
    """取编号对应的队伍名（账号下拉框显示用）；取不到返回 None。"""
    item = load_teams().get(str(index))
    if isinstance(item, dict):
        return item.get("名称") or item.get("秘境")
    if isinstance(item, str):       # 兼容只写了名字的老格式
        return item
    return None
