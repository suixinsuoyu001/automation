"""账号存储。

- **原神**：games/ys/data/账号.json —— **唯一数据源**，游戏脚本
  （games/ys/action/ys_action.py 的 账号json / 获取账号）读的就是这份。
  每条含「账号」和「启用」：GUI 账号页勾选启用哪几个，任务卡片的下拉框
  就只列启用的那几个（值仍是编号，和 队伍.json 的编号对齐）。
- **崩铁**：automation_gui/accounts.json（沿用原来的列表格式）。
"""
import json
import os

from automation_gui import config

# 原神账号表（与 games/ys/action/ys_action.py 里的 账号json 保持一致）
YS_ACCOUNTS_FILE = os.path.join(config.ROOT_DIR, "games", "ys", "data", "账号.json")


# ---------------------------------------------------------------------------
# 原神账号表（编号 -> {'账号', '启用'}）
# ---------------------------------------------------------------------------

def default_ys_accounts():
    """默认原神账号表：按 config.DEFAULT_YS_ACCOUNTS 的编号生成，默认全部启用。"""
    return {str(index): {"账号": account, "启用": True}
            for index, account in enumerate(config.DEFAULT_YS_ACCOUNTS)}


def load_ys_accounts():
    """读取原神账号表；文件不存在就按默认创建，保证游戏脚本一定读得到。

    返回 {'0': {'账号': '...', '启用': True}, ...}。
    兼容「值直接是账号字符串」的老格式（自动补上 启用=True）。
    """
    if not os.path.exists(YS_ACCOUNTS_FILE):
        data = default_ys_accounts()
        save_ys_accounts(data)
        return data
    try:
        with open(YS_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default_ys_accounts()
        fixed = {}
        for key, item in data.items():
            if isinstance(item, dict):
                fixed[str(key)] = {
                    "账号": str(item.get("账号", "")),
                    "启用": bool(item.get("启用", True)),
                }
            else:
                fixed[str(key)] = {"账号": str(item), "启用": True}
        return fixed
    except Exception:
        return default_ys_accounts()


def save_ys_accounts(data):
    """写回原神账号表（中文不转义、缩进 2）。"""
    os.makedirs(os.path.dirname(YS_ACCOUNTS_FILE), exist_ok=True)
    with open(YS_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ys_account_rows():
    """[(编号 int, 账号, 启用 bool), ...]，按编号升序（**含**未启用的所有条目）。"""
    rows = []
    for key, item in load_ys_accounts().items():
        try:
            index = int(key)
        except (TypeError, ValueError):
            continue
        rows.append((index, item.get("账号", ""), bool(item.get("启用", True))))
    return sorted(rows, key=lambda row: row[0])


def enabled_ys_accounts():
    """[{'编号': int, '账号': str}, ...] 只含**启用**的；一个都没启用时退回全部。

    返回编号是为了让任务下拉框把「编号」当值传出去 —— 编号是稳定标识，
    和 games/ys/data/队伍.json 的键一一对应。
    """
    rows = ys_account_rows()
    enabled = [row for row in rows if row[2]]
    if not enabled:
        enabled = rows        # 全都没勾选时不给空下拉框，退回全部
    return [{"编号": index, "账号": account} for index, account, _ in enabled]


# ---------------------------------------------------------------------------
# 崩铁账号列表（沿用 accounts.json）
# ---------------------------------------------------------------------------

def _default_data():
    return {
        "ys": list(config.DEFAULT_YS_ACCOUNTS),
        "bt": list(config.DEFAULT_BT_ACCOUNTS),
    }


def load_accounts():
    """崩铁读 accounts.json；原神的 "ys" 直接取自 账号.json（只含启用的）。

    这样任何还在用 account_store.load_accounts()["ys"] 的旧代码也不会读到过期数据。
    """
    data = None
    if os.path.exists(config.ACCOUNTS_FILE):
        try:
            with open(config.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None
    if not isinstance(data, dict):
        data = _default_data()
    data.setdefault("bt", list(config.DEFAULT_BT_ACCOUNTS))
    data["ys"] = [item["账号"] for item in enabled_ys_accounts()]
    return data


def save_accounts(data):
    """只负责崩铁的列表；原神账号请用 save_ys_accounts（在账号页里改）。"""
    payload = {
        "ys": [item["账号"] for item in enabled_ys_accounts()],   # 镜像一份，便于对账
        "bt": list(data.get("bt", config.DEFAULT_BT_ACCOUNTS)),
    }
    with open(config.ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

