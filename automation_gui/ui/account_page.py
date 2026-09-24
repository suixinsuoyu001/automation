"""账号管理页：可视化编辑原神/崩铁账号列表。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    ListWidget,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)

from automation_gui.core import account_store


class AccountPage(QWidget):
    """账号管理页。"""

    accountsChanged = Signal()   # 账号列表有改动（供任务页刷新下拉选项）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AccountPage")
        # 原神：编号 -> {'账号', '启用'}，唯一数据源 games/ys/data/账号.json
        self.ys_data = account_store.load_ys_accounts()
        # 崩铁：沿用 automation_gui/accounts.json 的列表
        self.bt_data = list(account_store.load_accounts().get("bt", []))
        self.current_game = "ys"
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        root.addWidget(SubtitleLabel("账号管理", self))

        # 游戏切换
        switch = QHBoxLayout()
        self.ys_btn = PushButton("原神", self)
        self.bt_btn = PushButton("崩铁", self)
        self.ys_btn.clicked.connect(lambda: self._switch_game("ys"))
        self.bt_btn.clicked.connect(lambda: self._switch_game("bt"))
        switch.addWidget(self.ys_btn)
        switch.addWidget(self.bt_btn)
        switch.addStretch(1)
        root.addLayout(switch)

        # 列表
        self.list_widget = ListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self._load_selected)
        root.addWidget(self.list_widget, 1)

        # 编辑区
        edit = QHBoxLayout()
        self.input = LineEdit(self)
        self.input.setPlaceholderText("输入账号（邮箱或手机号）")
        edit.addWidget(self.input, 1)
        self.add_btn = PrimaryPushButton(FluentIcon.ADD, "添加", self)
        self.add_btn.clicked.connect(self._add)
        self.update_btn = PushButton(FluentIcon.SAVE, "更新选中", self)
        self.update_btn.clicked.connect(self._update)
        self.remove_btn = PushButton(FluentIcon.DELETE, "删除选中", self)
        self.remove_btn.clicked.connect(self._remove)
        self.toggle_btn = PushButton("启用/停用选中", self)
        self.toggle_btn.clicked.connect(self._toggle)
        edit.addWidget(self.add_btn)
        edit.addWidget(self.update_btn)
        edit.addWidget(self.remove_btn)
        edit.addWidget(self.toggle_btn)
        root.addLayout(edit)

        self.hint = BodyLabel(
            "原神账号表在 games/ys/data/账号.json（游戏脚本读的是同一份）；"
            "用「启用/停用选中」决定任务下拉框里出现哪几个账号。"
            "双击列表项可载入到输入框编辑。",
            self,
        )
        self.hint.setWordWrap(True)
        self.hint.setTextColor("#808080", "#909090")
        root.addWidget(self.hint)

    def _switch_game(self, game):
        self.current_game = game
        self._refresh_list()

    def _ys_rows(self):
        """把原神工作副本整理成 [(编号, 账号, 启用), ...]，按编号升序。"""
        rows = []
        for key, item in self.ys_data.items():
            try:
                index = int(key)
            except (TypeError, ValueError):
                continue
            rows.append((index, item.get("账号", ""), bool(item.get("启用", True))))
        return sorted(rows, key=lambda row: row[0])

    def _refresh_list(self):
        self.list_widget.clear()
        if self.current_game == "ys":
            for index, account, enabled in self._ys_rows():
                mark = "[启用]" if enabled else "[停用]"
                item = QListWidgetItem(f"{mark} {index}.  {account}")
                item.setData(Qt.UserRole, index)
                self.list_widget.addItem(item)
            return
        for idx, acc in enumerate(self.bt_data):
            item = QListWidgetItem(f"{idx}.  {acc}")
            item.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item)

    def _load_selected(self, item):
        key = item.data(Qt.UserRole)
        if self.current_game == "ys":
            entry = self.ys_data.get(str(key))
            if entry:
                self.input.setText(entry.get("账号", ""))
            return
        if isinstance(key, int) and 0 <= key < len(self.bt_data):
            self.input.setText(self.bt_data[key])

    def _selected_key(self):
        """选中项的键：原神是编号，崩铁是下标。"""
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _add(self):
        text = self.input.text().strip()
        if not text:
            self._warn("请输入账号")
            return
        if self.current_game == "ys":
            # 新账号用「当前最大编号 + 1」，编号不复用，避免和队伍表/任务对上不
            index = max([row[0] for row in self._ys_rows()], default=-1) + 1
            self.ys_data[str(index)] = {"账号": text, "启用": True}
        else:
            self.bt_data.append(text)
        self._save()
        self.input.clear()

    def _update(self):
        key = self._selected_key()
        if key is None:
            self._warn("请先选择要更新的账号")
            return
        text = self.input.text().strip()
        if not text:
            self._warn("请输入账号")
            return
        if self.current_game == "ys":
            entry = self.ys_data.setdefault(str(key), {"账号": "", "启用": True})
            entry["账号"] = text
        else:
            self.bt_data[key] = text
        self._save()

    def _remove(self):
        key = self._selected_key()
        if key is None:
            self._warn("请先选择要删除的账号")
            return
        if self.current_game == "ys":
            self.ys_data.pop(str(key), None)
        else:
            del self.bt_data[key]
        self._save()
        self.input.clear()

    def _toggle(self):
        """启用 / 停用选中的原神账号（停用的不会出现在任务下拉框里）。"""
        key = self._selected_key()
        if key is None:
            self._warn("请先选择要启用/停用的账号")
            return
        if self.current_game != "ys":
            self._warn("崩铁账号没有启用开关")
            return
        entry = self.ys_data.get(str(key))
        if entry is None:
            return
        entry["启用"] = not bool(entry.get("启用", True))
        state = "已启用" if entry["启用"] else "已停用"
        self._save(content=f"编号 {key} {state}，任务下拉框已同步")

    def _save(self, content="账号列表已更新"):
        if self.current_game == "ys":
            account_store.save_ys_accounts(self.ys_data)
            self.ys_data = account_store.load_ys_accounts()   # 回读，保证与磁盘一致
        else:
            account_store.save_accounts({"bt": self.bt_data})
            self.bt_data = list(account_store.load_accounts().get("bt", []))
        self._refresh_list()
        self.accountsChanged.emit()
        InfoBar.success(
            title="已保存",
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self,
        )

    def _warn(self, msg):
        InfoBar.warning(
            title="提示",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )
