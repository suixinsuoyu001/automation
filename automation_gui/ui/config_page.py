"""秘境配置页：可视化编辑「圣遗物秘境编号 -> 模板图片名」映射。

数据落在 games/ys/data/秘境圣遗物.json，游戏脚本
games/ys/action/ys_action.py 读取的是**同一份文件**，所以在这里改完，
任务执行时用的就是新配置，不用改代码也不用重启。

选中列表项时，右侧会预览该条目对应的模板图片（games/ys/image/<名称>.png），
方便确认「名字有没有指错图」。
"""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
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
    StrongBodyLabel,
    SubtitleLabel,
)

from automation_gui import config
from automation_gui.core import domain_store

# 预览区尺寸（模板图约 200x95，这里留出少量余量；只等比缩小、不放大，
# 这样看到的模板就是真实像素大小，方便判断匹配质量）
PREVIEW_WIDTH = 320
PREVIEW_HEIGHT = 150

# 模板图是带透明通道的 PNG，铺一层中灰底，浅色/深色主题下都看得清
PREVIEW_BG = QColor(128, 128, 128)


class ConfigPage(QWidget):
    """圣遗物秘境配置页。"""

    domainsChanged = Signal()   # 配置有改动（供任务页刷新下拉选项）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConfigPage")
        self.data = domain_store.load_domains()
        self._build_ui()
        self._refresh_list()
        # 默认选中第一项，打开页面就能直接看到一张图
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        root.addWidget(SubtitleLabel("圣遗物秘境配置", self))

        hint = BodyLabel(f"数据文件：{domain_store.DOMAIN_FILE}", self)
        hint.setTextColor("#808080", "#909090")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # 左侧列表 + 右侧图片预览
        content = QHBoxLayout()
        content.setSpacing(12)

        self.list_widget = ListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self._load_selected)
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        content.addWidget(self.list_widget, 1)
        content.addLayout(self._build_preview())

        root.addLayout(content, 1)

        # 编辑区：编号 + 模板图片名
        edit = QHBoxLayout()
        self.index_input = LineEdit(self)
        self.index_input.setPlaceholderText("编号，如 1")
        self.index_input.setFixedWidth(90)
        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText(
            "模板图片名，如 圣遗物_虹灵的净土（对应 games/ys/image 下的同名 png）"
        )
        edit.addWidget(BodyLabel("编号:", self))
        edit.addWidget(self.index_input)
        edit.addWidget(BodyLabel("名称:", self))
        edit.addWidget(self.name_input, 1)
        root.addLayout(edit)

        buttons = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FluentIcon.ADD, "添加", self)
        self.add_btn.clicked.connect(self._add)
        self.update_btn = PushButton(FluentIcon.SAVE, "更新选中", self)
        self.update_btn.clicked.connect(self._update)
        self.remove_btn = PushButton(FluentIcon.DELETE, "删除选中", self)
        self.remove_btn.clicked.connect(self._remove)
        self.reset_btn = PushButton(FluentIcon.SYNC, "恢复默认", self)
        self.reset_btn.clicked.connect(self._reset)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.update_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addWidget(self.reset_btn)
        buttons.addStretch(1)
        root.addLayout(buttons)

        tip = BodyLabel("双击列表项可载入到输入框编辑；保存后任务卡片的秘境下拉框会自动更新", self)
        tip.setTextColor("#808080", "#909090")
        root.addWidget(tip)

    def _build_preview(self):
        """右侧图片预览区。"""
        box = QVBoxLayout()
        box.setSpacing(6)

        self.preview = QLabel(self)
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFrameShape(QFrame.Box)   # 透明模板图也能看出边界
        self.preview.setWordWrap(True)
        box.addWidget(self.preview)

        self.preview_name = StrongBodyLabel("", self)
        self.preview_name.setWordWrap(True)
        box.addWidget(self.preview_name)

        self.preview_info = BodyLabel("", self)
        self.preview_info.setTextColor("#808080", "#909090")
        self.preview_info.setWordWrap(True)
        box.addWidget(self.preview_info)

        box.addStretch(1)
        return box

    @staticmethod
    def _sort_key(key):
        """数字编号在前并按大小排，非数字编号排在后面。"""
        try:
            return (0, int(key))
        except (TypeError, ValueError):
            return (1, str(key))

    def _refresh_list(self, select_key=None):
        """重建列表，并尽量保留原来的选中项。"""
        if select_key is None:
            select_key = self._selected_key()
        # 重建期间屏蔽信号，避免反复触发预览刷新
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for key in sorted(self.data, key=self._sort_key):
            item = QListWidgetItem(f"{key}  →  {self.data[key]}")
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)
            if select_key is not None and str(key) == str(select_key):
                self.list_widget.setCurrentItem(item)
        self.list_widget.blockSignals(False)
        # setCurrentItem 的信号被屏蔽了，这里补一次预览
        self._show_preview(self.data.get(self._selected_key()))

    # ------------------------------------------------------------------
    # 图片预览
    # ------------------------------------------------------------------
    @staticmethod
    def _image_path(name):
        """模板图片路径：games/ys/image/<名称>.png。"""
        return os.path.join(
            config.ROOT_DIR, "games", "ys", "image", f"{name}.png"
        )

    def _on_selection_changed(self, current, previous):
        """列表选中项变化 -> 刷新右侧预览。"""
        if current is None:
            self._show_preview(None)
            return
        self._show_preview(self.data.get(current.data(Qt.UserRole)))

    def _show_preview(self, name):
        """把 name 对应的模板图片画到预览区；找不到图片时给出提示。"""
        if not name:
            self.preview.setPixmap(QPixmap())      # 清掉上一次的图
            self.preview.setText("请在左侧选择一个条目")
            self.preview_name.setText("")
            self.preview_info.setText("")
            return

        name = str(name)
        path = self._image_path(name)
        pix = QPixmap(path)
        if pix.isNull():
            self.preview.setPixmap(QPixmap())
            self.preview.setText(f"未找到图片：{name}.png")
            self.preview_name.setText(name)
            self.preview_info.setText(f"期望路径：{path}")
            return

        original = pix.size()
        # 等比缩放到预览框内（不放大超过原图尺寸，避免糊）
        width = min(PREVIEW_WIDTH, max(original.width(), 1))
        height = min(PREVIEW_HEIGHT, max(original.height(), 1))
        scaled = pix.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 模板图是带透明通道的 PNG，铺一层中灰底，浅色/深色主题下都看得清
        canvas = QPixmap(scaled.size())
        canvas.fill(PREVIEW_BG)
        painter = QPainter(canvas)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

        self.preview.setPixmap(canvas)
        self.preview_name.setText(name)
        self.preview_info.setText(
            f"原始尺寸：{original.width()} x {original.height()} px\n{path}"
        )

    # ------------------------------------------------------------------
    # 编辑操作
    # ------------------------------------------------------------------
    def _load_selected(self, item):
        """双击列表项 -> 载入到输入框。"""
        key = item.data(Qt.UserRole)
        self.index_input.setText(str(key))
        self.name_input.setText(str(self.data.get(key, "")))

    def _selected_key(self):
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _read_inputs(self):
        """校验输入，返回 (编号字符串, 名称)；不合法返回 None。"""
        index = self.index_input.text().strip()
        name = self.name_input.text().strip()
        if not index:
            self._warn("请输入秘境编号")
            return None
        if not index.lstrip("+-").isdigit():
            self._warn("秘境编号必须是数字")
            return None
        if not name:
            self._warn("请输入模板图片名")
            return None
        return str(int(index)), name

    def _add(self):
        result = self._read_inputs()
        if result is None:
            return
        index, name = result
        if index in self.data:
            self._warn(f"编号 {index} 已存在，请改用「更新选中」")
            return
        self.data[index] = name
        self._save()

    def _update(self):
        result = self._read_inputs()
        if result is None:
            return
        index, name = result
        old_key = self._selected_key()
        if old_key is None:
            self._warn("请先选择要更新的条目")
            return
        if str(old_key) != index:
            self.data.pop(str(old_key), None)   # 编号被改了，移除旧项
        self.data[index] = name
        self._save()

    def _remove(self):
        key = self._selected_key()
        if key is None:
            self._warn("请先选择要删除的条目")
            return
        self.data.pop(str(key), None)
        self._save()

    def _reset(self):
        self.data = domain_store.default_domains()
        self.index_input.clear()
        self.name_input.clear()
        self._save()

    def _save(self):
        domain_store.save_domains(self.data)
        self.data = domain_store.load_domains()   # 回读，保证与磁盘一致
        self._refresh_list()
        self.domainsChanged.emit()
        InfoBar.success(
            title="已保存",
            content="秘境配置已更新，任务下拉框已同步",
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
