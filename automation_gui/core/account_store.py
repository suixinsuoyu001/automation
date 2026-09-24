"""账号存储：读写 accounts.json。"""
import json
import os

from automation_gui import config


def _default_data():
    return {
        "ys": list(config.DEFAULT_YS_ACCOUNTS),
        "bt": list(config.DEFAULT_BT_ACCOUNTS),
    }


def load_accounts():
    if not os.path.exists(config.ACCOUNTS_FILE):
        data = _default_data()
        save_accounts(data)
        return data
    try:
        with open(config.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("ys", list(config.DEFAULT_YS_ACCOUNTS))
        data.setdefault("bt", list(config.DEFAULT_BT_ACCOUNTS))
        return data
    except Exception:
        return _default_data()


def save_accounts(data):
    with open(config.ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
