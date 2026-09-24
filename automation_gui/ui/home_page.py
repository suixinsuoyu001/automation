"""首页：任务卡片列表 + 开始/停止控制。

风格参考 ok-ww：顶部按游戏切换（跟账号页一样先选游戏），下面**一行两个**卡片，
底部「开始任务 / 停止任务」。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SegmentedWidget,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
)

from automation_gui import config
from automation_gui.core import tasks as task_registry

# 卡片统一高度，保证两列对齐；同时也够放「标题 + 两行描述 + 一行参数」
CARD_HEIGHT = 132

# 一行放几个卡片
CARDS_PER_ROW = 2

# 下拉框最小宽度（一行两个卡片，宽度有限）
COMBO_MIN_WIDTH = 200


class TaskCard(CardWidget):
    """单个任务卡片：单选 + 名称 + 描述 + 参数。"""

    def __init__(self, task: task_registry.TaskDef, parent=None):
        super().__init__(parent)
        self.task = task
        self.param_widgets = {}

        self.setFixedHeight(CARD_HEIGHT)
        self.setToolTip(f"{task.name}\n{task.description}\n\n入口: {task.entry}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self.radio = RadioButton(self)
        layout.addWidget(self.radio, 0, Qt.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        self.title = StrongBodyLabel(task.name, self)
        self.desc = BodyLabel(task.description, self)
        self.desc.setWordWrap(True)
        self.desc.setTextColor("#606060", "#a0a0a0")
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.desc)

        if task.params:
            param_layout = QHBoxLayout()
            param_layout.setSpacing(8)
            for p in task.params:
                param_layout.addWidget(BodyLabel(f"{p.label}:", self))
                if p.type == "choice":
                    # 下拉选择：显示名称，实际取值仍是原始编号
                    combo = ComboBox(self)
                    combo.setMinimumWidth(COMBO_MIN_WIDTH)
                    self._fill_combo(combo, p)
                    self.param_widgets[p.key] = combo
                    param_layout.addWidget(combo, 1)
                else:
                    spin = QSpinBox(self)
                    spin.setRange(p.minimum, p.maximum)
                    spin.setValue(int(p.default))
                    spin.setFixedWidth(78)
                    self.param_widgets[p.key] = spin
                    param_layout.addWidget(spin)
                param_layout.addSpacing(6)
            param_layout.addStretch(1)
            text_layout.addLayout(param_layout)

        text_layout.addStretch(1)
        layout.addLayout(text_layout, 1)

    @staticmethod
    def _fill_combo(combo, param, keep=None):
        """把参数选项填进下拉框，并尽量保持当前选中项。"""
        combo.blockSignals(True)
        combo.clear()
        for value, text in param.option_list():
            combo.addItem(text, userData=value)
        target = param.default if keep is None else keep
        index = combo.findData(target)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def param_values(self):
        """当前参数值（下拉框取 userData，保证传回任务函数的是原始编号）。"""
        values = {}
        for key, widget in self.param_widgets.items():
            if isinstance(widget, ComboBox):
                values[key] = widget.currentData()
            else:
                values[key] = widget.value()
        return values

    def refresh_params(self):
        """账号/秘境配置变化后重新填充下拉选项，保留用户当前的选择。"""
        for p in self.task.params:
            if p.type != "choice":
                continue
            combo = self.param_widgets.get(p.key)
            if combo is not None:
                self._fill_combo(combo, p, keep=combo.currentData())


class TaskSwitchRow(CardWidget):
    """开关型任务（自动剧情这类持续任务）：名称 + 说明 + 开关。

    和卡片不同，它不是「选中 -> 点开始」，而是直接拨开关：
    打开=开始任务，关闭=停止任务。
    """

    toggled = Signal(str, bool)      # task_id, 是否打开

    def __init__(self, task: task_registry.TaskDef, parent=None):
        super().__init__(parent)
        self.task = task
        self.setToolTip(f"{task.name}\n{task.description}\n\n入口: {task.entry}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(StrongBodyLabel(task.name, self))
        desc = BodyLabel(task.description, self)
        desc.setWordWrap(True)
        desc.setTextColor("#606060", "#a0a0a0")
        text_layout.addWidget(desc)
        layout.addLayout(text_layout, 1)

        self.switch = SwitchButton(self)
        self.switch.setOnText("开")
        self.switch.setOffText("关")
        layout.addWidget(self.switch, 0, Qt.AlignVCenter)

        # 程序同步状态时不要把信号再弹回去
        self._silent = False
        self.switch.checkedChanged.connect(self._on_checked_changed)

    def _on_checked_changed(self, checked):
        if self._silent:
            return
        self.toggled.emit(self.task.id, bool(checked))

    def set_on(self, on):
        """由程序同步开关状态（不会触发 toggled）。"""
        on = bool(on)
        if self.switch.isChecked() == on:
            return
        self._silent = True
        try:
            self.switch.setChecked(on)
        finally:
            self._silent = False

    def is_on(self):
        return self.switch.isChecked()


class HomePage(QWidget):
    """首页。"""

    startRequested = Signal(str, dict)   # task_id, kwargs
    stopRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePage")
        self.cards = []                  # 全部卡片（含当前隐藏的）
        self._cards = {}                 # task_id -> TaskCard
        self._switch_rows = {}           # task_id -> TaskSwitchRow（开关型任务）
        self._running_task_id = None     # 当前正在跑的任务
        self._current_game = config.DEFAULT_GAME
        self._build_ui()
        # 默认展示原神；切换控件也同步选中
        self.game_switch.setCurrentItem(self._current_game)
        self._populate(self._current_game)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(SubtitleLabel("任务列表", self))
        header.addStretch(1)
        self.status_label = BodyLabel("就绪", self)
        header.addWidget(self.status_label)
        root.addLayout(header)

        # 游戏切换（和账号页一样：先选游戏，再展示该游戏的任务）
        self.game_switch = SegmentedWidget(self)
        for game in task_registry.tasks_by_group().keys():
            self.game_switch.addItem(game, game)
        # 统一用 currentItemChanged：点击切换、以及程序 setCurrentItem 都会走到这里
        self.game_switch.currentItemChanged.connect(self._populate)
        root.addWidget(self.game_switch)

        # 卡片区：一行 CARDS_PER_ROW 个
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 8, 0)
        outer.setSpacing(10)

        # 开关型任务区（自动剧情这类持续任务），放在卡片网格上面
        self.switch_area = QVBoxLayout()
        self.switch_area.setSpacing(10)
        outer.addLayout(self.switch_area)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        outer.addLayout(self.grid)
        outer.addStretch(1)
        scroll.setWidget(container)
        self._container = container
        root.addWidget(scroll, 1)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        # 卡片 / 开关行都只建一次，切换游戏时只是搬进/搬出布局，
        # 这样用户选好的参数不会因为切游戏被重置
        for task in task_registry.ALL_TASKS:
            if task.switch:
                row = TaskSwitchRow(task, container)
                row.toggled.connect(self._on_switch_toggled)
                row.hide()
                self._switch_rows[task.id] = row
                continue
            card = TaskCard(task, container)
            self.group.addButton(card.radio)
            card.hide()
            self._cards[task.id] = card
            self.cards.append(card)

        # 底部操作栏
        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        self.start_btn = PrimaryPushButton(FluentIcon.PLAY, "开始任务", self)
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn = PushButton(FluentIcon.CANCEL, "停止任务", self)
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        bottom.addStretch(1)
        bottom.addWidget(self.start_btn)
        bottom.addWidget(self.stop_btn)
        root.addLayout(bottom)

    # ------------------------------------------------------------------
    # 游戏切换
    # ------------------------------------------------------------------
    @staticmethod
    def games():
        """当前有哪些游戏分组。"""
        return list(task_registry.tasks_by_group().keys())

    def _populate(self, game):
        """按游戏把卡片放进网格（一行 CARDS_PER_ROW 个）。"""
        if game not in self.games():
            return
        self._current_game = game
        # 顶部切换控件保持同步（用 routeKey 比较；已经是当前项时
        # setCurrentItem 会直接返回，不会再次发信号，所以不会递归）
        if self.game_switch.currentRouteKey() != game:
            self.game_switch.setCurrentItem(game)

        # 先把两个区域清空并隐藏 —— 控件对象一直保留，
        # 所以用户在另一个游戏里选好的参数不会因为切游戏被重置
        while self.grid.count():
            self.grid.takeAt(0)
        while self.switch_area.count():
            self.switch_area.takeAt(0)
        for card in self.cards:
            card.hide()
        for row in self._switch_rows.values():
            row.hide()

        game_tasks = [t for t in task_registry.ALL_TASKS if t.group == game]

        # 开关型任务（自动剧情）排在最上面
        for task in game_tasks:
            if not task.switch:
                continue
            row = self._switch_rows[task.id]
            self.switch_area.addWidget(row)
            row.show()

        # 其余任务按「一行两个」铺网格
        index = 0
        for task in game_tasks:
            if task.switch:
                continue
            card = self._cards[task.id]
            self.grid.addWidget(card, index // CARDS_PER_ROW, index % CARDS_PER_ROW)
            card.show()
            index += 1

        # 切游戏后原选中项若被藏起来了就清掉选择，
        # 否则「开始任务」会跑到一个看不见的任务上。
        # ⚠ 这里必须扫**全部**卡片：_current_game 已经切过来了，
        # 用只看可见卡片的 _selected_card() 会找不到旧游戏的选中项。
        for card in self.cards:
            if card.task.group == game or not card.radio.isChecked():
                continue
            self.group.setExclusive(False)
            card.radio.setChecked(False)
            self.group.setExclusive(True)
            break

    def current_game(self):
        return self._current_game

    def show_game(self, game):
        """切到指定游戏（外部调用，比如登录快捷键）。"""
        if game in self.games():
            self._populate(game)

    # ------------------------------------------------------------------
    # 任务控制
    # ------------------------------------------------------------------
    def _visible_cards(self):
        return [c for c in self.cards if c.task.group == self._current_game]

    def _selected_card(self):
        """只在**当前可见**的卡片里找选中项。"""
        for card in self._visible_cards():
            if card.radio.isChecked():
                return card
        return None

    def _on_start(self):
        card = self._selected_card()
        if card is None:
            InfoBar.warning(
                title="未选择任务",
                content="请先选择一个要执行的任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return
        self.startRequested.emit(card.task.id, card.param_values())

    def _on_stop(self):
        self.stopRequested.emit()

    def card_for(self, task_id):
        """按任务 id 找到卡片（含当前隐藏的）。"""
        return self._cards.get(task_id)

    def switch_for(self, task_id):
        """按任务 id 找到开关行（含当前隐藏的）。"""
        return self._switch_rows.get(task_id)

    def latest_switch(self, game=None):
        """某个游戏里第一个开关（用于快捷键）。"""
        for task in task_registry.ALL_TASKS:
            if task.switch and (game is None or task.group == game):
                return self._switch_rows.get(task.id)
        return None

    def _on_switch_toggled(self, task_id, on):
        """开关型任务：打开=开始任务，关闭=停止任务。"""
        if on:
            self.startRequested.emit(task_id, {})
            return
        # 关的时候只有「正在跑的就是它」才需要通知停止
        if self._running_task_id == task_id:
            self.stopRequested.emit()
        else:
            self.set_switch_state(task_id, False)

    def set_switch_state(self, task_id, on):
        """外部同步某个开关的状态（不会回调 startRequested / stopRequested）。

        例如启动失败时把它拨回关闭。
        """
        row = self._switch_rows.get(task_id)
        if row is not None:
            row.set_on(on)

    def set_switch_enabled(self, enabled):
        """统一启用/禁用所有开关（比如有任务在跑时不让乱拨）。"""
        for row in self._switch_rows.values():
            row.switch.setEnabled(enabled)

    def refresh_params(self, task_id=None):
        """刷新参数下拉选项（task_id 为 None 时刷新全部）。

        账号页 / 秘境配置页改完数据后调用，让下拉框立刻反映最新内容。
        """
        if task_id is None:
            for card in self.cards:
                card.refresh_params()
            return
        card = self._cards.get(task_id)
        if card is not None:
            card.refresh_params()

    def set_running(self, running: bool, task_name: str = "", task_id=None):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self._running_task_id = task_id if running else None
        # 开关状态跟着实际运行情况走：只有正在跑的那个是「开」
        for tid, row in self._switch_rows.items():
            row.set_on(bool(running) and tid == task_id)
        if running:
            self.status_label.setText(f"运行中: {task_name}")
        else:
            self.status_label.setText("就绪")
