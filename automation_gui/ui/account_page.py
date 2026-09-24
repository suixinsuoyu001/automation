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
        self.data = account_store.load_accounts()
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
        edit.addWidget(self.add_btn)
        edit.addWidget(self.update_btn)
        edit.addWidget(self.remove_btn)
        root.addLayout(edit)

        self.hint = BodyLabel("双击列表项可载入到输入框进行编辑", self)
        self.hint.setTextColor("#808080", "#909090")
        root.addWidget(self.hint)

    def _switch_game(self, game):
        self.current_game = game
        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for idx, acc in enumerate(self.data.get(self.current_game, [])):
            item = QListWidgetItem(f"{idx}.  {acc}")
            item.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item)

    def _load_selected(self, item):
        idx = item.data(Qt.UserRole)
        accounts = self.data.get(self.current_game, [])
        if 0 <= idx < len(accounts):
            self.input.setText(accounts[idx])

    def _selected_index(self):
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _add(self):
        text = self.input.text().strip()
        if not text:
            self._warn("请输入账号")
            return
        self.data.setdefault(self.current_game, []).append(text)
        self._save()
        self.input.clear()

    def _update(self):
        idx = self._selected_index()
        if idx is None:
            self._warn("请先选择要更新的账号")
            return
        text = self.input.text().strip()
        if not text:
            self._warn("请输入账号")
            return
        self.data[self.current_game][idx] = text
        self._save()

    def _remove(self):
        idx = self._selected_index()
        if idx is None:
            self._warn("请先选择要删除的账号")
            return
        del self.data[self.current_game][idx]
        self._save()
        self.input.clear()

    def _save(self):
        account_store.save_accounts(self.data)
        self._refresh_list()
        self.accountsChanged.emit()
        InfoBar.success(
            title="已保存",
            content="账号列表已更新",
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
