import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog, QToolBar, QStatusBar)
from PyQt6.QtGui import (QPixmap, QPainter, QPen, QColor, QFont,
                         QScreen, QGuiApplication, QCursor)
from PyQt6.QtCore import Qt, QRect, QPoint


class ScreenshotTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupShortcuts()

        # 截图相关变量
        self.screenshot = None
        self.drawing = False
        self.lastPoint = QPoint()
        self.current_shape = "rectangle"  # 默认绘制矩形
        self.shapes = []  # 存储所有绘制的形状
        self.is_selecting = False  # 是否正在选择区域
        self.selection_start = QPoint()
        self.selection_end = QPoint()

        # 画笔设置
        self.pen_color = QColor(255, 0, 0)  # 红色
        self.pen_width = 3

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle('PyQt6 截图工具')
        self.setGeometry(100, 100, 800, 600)

        # 中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 布局
        self.layout = QVBoxLayout(self.central_widget)

        # 工具栏
        self.toolbar = QToolBar("主工具栏")
        self.addToolBar(self.toolbar)

        # 截图按钮
        self.fullscreen_btn = QPushButton("全屏截图", self)
        self.fullscreen_btn.clicked.connect(self.captureFullScreen)
        self.toolbar.addWidget(self.fullscreen_btn)

        self.area_btn = QPushButton("区域截图", self)
        self.area_btn.clicked.connect(self.startAreaSelection)
        self.toolbar.addWidget(self.area_btn)

        # 绘制工具按钮
        self.rect_btn = QPushButton("矩形", self)
        self.rect_btn.clicked.connect(lambda: self.setDrawingShape("rectangle"))
        self.toolbar.addWidget(self.rect_btn)

        self.arrow_btn = QPushButton("箭头", self)
        self.arrow_btn.clicked.connect(lambda: self.setDrawingShape("arrow"))
        self.toolbar.addWidget(self.arrow_btn)

        self.text_btn = QPushButton("文字", self)
        self.text_btn.clicked.connect(lambda: self.setDrawingShape("text"))
        self.toolbar.addWidget(self.text_btn)

        # 保存按钮
        self.save_btn = QPushButton("保存", self)
        self.save_btn.clicked.connect(self.saveScreenshot)
        self.toolbar.addWidget(self.save_btn)

        # 显示截图的标签
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: white;")
        self.layout.addWidget(self.image_label)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")

    def setupShortcuts(self):
        """设置快捷键"""
        # 这里可以添加各种快捷键，例如 Esc 取消选择区域等
        pass

    def captureFullScreen(self):
        """捕获全屏截图"""
        screen = QGuiApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        self.showScreenshot()
        self.status_bar.showMessage("全屏截图已捕获")

    def startAreaSelection(self):
        """开始区域选择"""
        self.hide()  # 隐藏主窗口
        self.is_selecting = True
        self.selection_start = QPoint()
        self.selection_end = QPoint()

        # 创建一个透明窗口用于选择区域
        self.selection_window = QWidget()
        self.selection_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.selection_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.selection_window.setGeometry(QGuiApplication.primaryScreen().geometry())

        # 使用QPixmap捕获屏幕作为背景
        screen = QGuiApplication.primaryScreen()
        bg_pixmap = screen.grabWindow(0)
        self.selection_window.bg_pixmap = bg_pixmap

        # 自定义绘制
        self.selection_window.paintEvent = self.selectionWindowPaintEvent
        self.selection_window.mousePressEvent = self.selectionMousePressEvent
        self.selection_window.mouseMoveEvent = self.selectionMouseMoveEvent
        self.selection_window.mouseReleaseEvent = self.selectionMouseReleaseEvent
        self.selection_window.keyPressEvent = self.selectionKeyPressEvent

        self.selection_window.showFullScreen()

    def selectionWindowPaintEvent(self, event):
        """选择区域窗口的绘制事件"""
        painter = QPainter(self.selection_window)
        painter.drawPixmap(0, 0, self.selection_window.bg_pixmap)

        # 绘制半透明遮罩
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.selection_window.width(), self.selection_window.height())

        # 如果有选择区域，绘制选中区域（不覆盖半透明层）
        if not self.selection_start.isNull() and not self.selection_end.isNull():
            rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.drawPixmap(rect, self.selection_window.bg_pixmap, rect)

            # 绘制边框
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.DashLine))
            painter.drawRect(rect)

            # 显示区域大小
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                rect.bottomRight() + QPoint(5, 15),
                f"{rect.width()} x {rect.height()}"
            )

    def selectionMousePressEvent(self, event):
        """选择区域时的鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selection_window.update()

    def selectionMouseMoveEvent(self, event):
        """选择区域时的鼠标移动事件"""
        if not self.selection_start.isNull():
            self.selection_end = event.pos()
            self.selection_window.update()

    def selectionMouseReleaseEvent(self, event):
        """选择区域时的鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.selection_start.isNull() and not self.selection_end.isNull():
                # 获取选择的区域
                rect = QRect(self.selection_start, self.selection_end).normalized()
                screen = QGuiApplication.primaryScreen()
                self.screenshot = screen.grabWindow(0,
                                                    rect.x(), rect.y(),
                                                    rect.width(), rect.height())
                self.selection_window.close()
                self.show()
                self.showScreenshot()
                self.status_bar.showMessage(f"区域截图已捕获: {rect.width()}x{rect.height()}")

    def selectionKeyPressEvent(self, event):
        """选择区域时的按键事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.selection_window.close()
            self.show()
            self.status_bar.showMessage("区域选择已取消")

    def showScreenshot(self):
        """显示截图"""
        if self.screenshot:
            self.image_label.setPixmap(self.screenshot.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def setDrawingShape(self, shape):
        """设置当前绘制的形状"""
        self.current_shape = shape
        self.status_bar.showMessage(f"当前工具: {shape}")

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始绘制"""
        if event.button() == Qt.MouseButton.LeftButton and self.screenshot:
            self.drawing = True
            self.lastPoint = event.pos()

            if self.current_shape == "text":
                # 如果是文本工具，直接添加文本
                self.addText(event.pos())
                self.drawing = False

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 绘制中"""
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing and self.screenshot:
            painter = QPainter(self.screenshot)
            painter.setPen(QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine))

            if self.current_shape == "rectangle":
                # 临时绘制矩形（实际绘制在mouseReleaseEvent中完成）
                pass
            elif self.current_shape == "arrow":
                # 临时绘制箭头
                pass

            self.showScreenshot()
            self.lastPoint = event.pos()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 完成绘制"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing and self.screenshot:
            painter = QPainter(self.screenshot)
            painter.setPen(QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine))

            if self.current_shape == "rectangle":
                rect = QRect(self.lastPoint, event.pos()).normalized()
                painter.drawRect(rect)
                self.shapes.append(("rectangle", rect, self.pen_color, self.pen_width))
            elif self.current_shape == "arrow":
                self.drawArrow(painter, self.lastPoint, event.pos())
                self.shapes.append(("arrow", (self.lastPoint, event.pos()), self.pen_color, self.pen_width))

            painter.end()
            self.drawing = False
            self.showScreenshot()

    def drawArrow(self, painter, start, end):
        """绘制箭头"""
        painter.drawLine(start, end)

        # 计算箭头头部
        angle = start.angleTo(end)
        arrow_size = 10

        # 绘制箭头两侧的线
        # 这里简化了箭头绘制，实际可以更复杂
        line = end - start
        line_length = (line.x() ** 2 + line.y() ** 2) ** 0.5
        if line_length == 0:
            return

        dx = line.x() / line_length
        dy = line.y() / line_length

        left = QPointF(
            end.x() - arrow_size * (dx * 0.866 + dy * 0.5),
            end.y() - arrow_size * (dy * 0.866 - dx * 0.5)
        )
        right = QPointF(
            end.x() - arrow_size * (dx * 0.866 - dy * 0.5),
            end.y() - arrow_size * (dy * 0.866 + dx * 0.5)
        )

        painter.drawLine(end, left)
        painter.drawLine(end, right)

    def addText(self, position):
        """添加文本到截图"""
        # 这里简化了文本输入，实际可以使用QInputDialog或自定义对话框
        text, ok = QInputDialog.getText(self, "添加文本", "输入文本:")
        if ok and text:
            painter = QPainter(self.screenshot)
            painter.setPen(self.pen_color)
            font = QFont("Arial", 12)
            painter.setFont(font)
            painter.drawText(position, text)
            painter.end()

            self.shapes.append(("text", (position, text), self.pen_color, font))
            self.showScreenshot()

    def saveScreenshot(self):
        """保存截图到文件"""
        if not self.screenshot:
            self.status_bar.showMessage("没有可保存的截图")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存截图", "",
            "PNG图像 (*.png);;JPEG图像 (*.jpg *.jpeg);;所有文件 (*)"
        )

        if file_path:
            if file_path.endswith(('.png', '.jpg', '.jpeg')):
                format = file_path[-3:].upper()
            else:
                file_path += '.png'
                format = 'PNG'

            self.screenshot.save(file_path, format)
            self.status_bar.showMessage(f"截图已保存到: {file_path}")

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.showScreenshot()


def main():
    # 设置高 DPI 缩放策略
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    # ... 你的其他代码 ...
    sys.exit(app.exec())

if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = ScreenshotTool()
    window.show()
    sys.exit(app.exec())