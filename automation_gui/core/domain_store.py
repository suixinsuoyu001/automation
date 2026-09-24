"""圣遗物秘境配置存储：读写 games/ys/data/秘境圣遗物.json。

这份映射表同时被游戏脚本 `games/ys/action/ys_action.py` 读取
（见其中的 `秘境圣遗物json`），所以在 GUI 里改完，任务执行时用的
就是新配置，不需要动代码。
"""
import json
import os

from automation_gui import config

# 与 games/ys/action/ys_action.py 里的 秘境圣遗物json 保持一致
DOMAIN_FILE = os.path.join(
    config.ROOT_DIR, "games", "ys", "data", "秘境圣遗物.json"
)


def default_domains():
    """默认映射（来自 config.YS_DOMAIN_NAMES）。"""
    return {str(num): name for num, name in sorted(config.YS_DOMAIN_NAMES.items())}


def load_domains():
    """读取映射表，返回 {'1': '圣遗物_虹灵的净土', ...}。

    文件不存在时用默认映射创建，保证游戏脚本一定读得到。
    """
    if not os.path.exists(DOMAIN_FILE):
        data = default_domains()
        save_domains(data)
        return data
    try:
        with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default_domains()
        return data
    except Exception:
        return default_domains()


def save_domains(data):
    """写回映射表（中文不转义、缩进 2，与 AutoFight.json 风格一致）。"""
    os.makedirs(os.path.dirname(DOMAIN_FILE), exist_ok=True)
    with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
