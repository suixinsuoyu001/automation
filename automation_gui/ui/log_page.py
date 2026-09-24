"""日志页：实时显示任务运行日志。"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    FluentIcon,
    PlainTextEdit,
    PushButton,
    SubtitleLabel,
)

_LEVEL_COLORS = {
    "info": "#d0d0d0",
    "success": "#4caf50",
    "error": "#f44336",
    "warning": "#ff9800",
}


class LogPage(QWidget):
    """日志页。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPage")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(SubtitleLabel("运行日志", self))
        header.addStretch(1)
        self.clear_btn = PushButton(FluentIcon.DELETE, "清空", self)
        self.clear_btn.clicked.connect(self.clear)
        header.addWidget(self.clear_btn)
        root.addLayout(header)

        self.view = PlainTextEdit(self)
        self.view.setReadOnly(True)
        self.view.setPlaceholderText("暂无日志")
        font = self.view.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.view.setFont(font)
        root.addWidget(self.view, 1)

    def append(self, message: str, level: str = "info"):
        color = _LEVEL_COLORS.get(level, "#d0d0d0")
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(message + "\n", fmt)
        self.view.setTextCursor(cursor)
        self.view.ensureCursorVisible()

    def clear(self):
        self.view.clear()
