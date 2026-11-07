"""主窗口：FluentWindow + 左侧导航，风格参考 ok-ww。"""
import multiprocessing
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLineEdit
from qfluentwidgets import (
    FluentIcon,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    NavigationItemPosition,
    setTheme,
    Theme,
)

from automation_gui import config
from automation_gui.core import tasks as task_registry
from automation_gui.core.task_runner import TaskRunner
from automation_gui.ui.account_page import AccountPage
from automation_gui.ui.config_page import ConfigPage
from automation_gui.ui.home_page import HomePage
from automation_gui.ui.log_page import LogPage

# 截图「彻底救不回来」（连续 CAPTURE_DEAD_SECONDS 秒一帧都没有，截图线程自己已经
# 换过好几次）时，要不要把整个任务进程杀掉重开。
#
# 默认 **False**：重开进程会连着把任务脚本自己起的点击子进程一起收掉，还会在重开
# 时 `focus_or_start_game()` 把游戏窗口抢回前台 —— 正在用电脑的人会被打断。所以
# 默认只把问题报出来（日志 + 右下角提示），由用户自己决定要不要重开。
# 想让程序自动重开就把它改成 True（最多重开 TaskRunner.MAX_RESTARTS 次）。
AUTO_RESTART_ON_CAPTURE_DEAD = False


class MainWindow(FluentWindow):
    # pynput 的键盘钩子跑在它自己的线程里，不能直接操作界面；
    # 用信号把按键转到 Qt 主线程再处理。
    loginHotkeyPressed = Signal(int)   # 前缀 + 数字 -> 登录第 N 个账号
    talkHotkeyPressed = Signal()       # 前缀 + t    -> 开/关原神自动剧情

    # 全局快捷键：前缀键 + 数字（默认 '+1' -> 第 1 个账号）
    # '+' 在键盘上是 Shift+= ，pynput 会把 char 报成 '+'
    快捷键前缀 = "+"

    # 前缀 + 这个键 -> 开/关原神自动剧情
    剧情快捷键 = "t"

    # 全局快捷键：前缀键与数字之间允许的最大间隔（秒）
    快捷键间隔 = 1.5

    # 前缀是 Shift+= 时，用户很可能还按着 Shift 就打数字，
    # 这时数字会变成上档符号 —— 一并认掉，手感更顺
    _上档数字 = {
        "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
        "^": "6", "&": "7", "*": "8", "(": "9",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_TITLE} {config.APP_VERSION}")
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        # 日志队列（子进程 -> UI）
        self.log_queue = multiprocessing.Queue()
        self.runner = TaskRunner(self.log_queue)
        self.current_task_id = None
        self.current_task_name = ""
        # 自动重开任务时用来忽略旧进程残留的「done」消息（时间戳，见 _poll_queue）
        self._restart_guard_until = 0.0
        # 进程不在了、但「done」还没到（还在队列管道里）时，先等一会儿再判死
        self._process_gone_at = None
        # 「截图彻底抓不到画面」只提示一次（重开进程默认关闭，见模块里的
        # AUTO_RESTART_ON_CAPTURE_DEAD）
        self._capture_dead_reported = False

        self.home_page = HomePage(self)
        self.account_page = AccountPage(self)
        self.config_page = ConfigPage(self)
        self.log_page = LogPage(self)

        self.home_page.startRequested.connect(self._start_task)
        self.home_page.stopRequested.connect(self._stop_task)
        # 账号页 / 秘境配置页改动后，任务卡片上的下拉框跟着更新
        self.account_page.accountsChanged.connect(self.home_page.refresh_params)
        self.config_page.domainsChanged.connect(self.home_page.refresh_params)

        self.addSubInterface(self.home_page, FluentIcon.HOME, "任务")
        self.addSubInterface(self.account_page, FluentIcon.PEOPLE, "账号")
        self.addSubInterface(self.config_page, FluentIcon.SETTING, "秘境配置")
        self.addSubInterface(self.log_page, FluentIcon.DOCUMENT, "日志")

        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FluentIcon.CONSTRACT,
            text="切换主题",
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM,
        )

        # 原神登录全局快捷键：g+1 ~ g+9（焦点在游戏窗口也生效）
        self._hotkey_pending = None
        self._hotkey_listener = None
        self.loginHotkeyPressed.connect(self._login_account)
        self.talkHotkeyPressed.connect(self._toggle_talk)
        self._setup_login_hotkeys()

        # 轮询日志队列
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._poll_queue)
        self.timer.start()

        self._log("程序已启动，请选择任务后点击「开始任务」", "info")

    # ------------------------------------------------------------------
    # 任务控制
    # ------------------------------------------------------------------
    def _start_task(self, task_id, values):
        task = task_registry.get_task(task_id)
        if task is None:
            return
        try:
            kwargs = task.build_kwargs(values)
            self.runner.start(task.entry, kwargs)
        except Exception as e:
            # 启动失败（一般是「已有任务正在运行」）——把刚拨开的开关拨回去
            self.home_page.set_switch_state(task_id, False)
            InfoBar.error(
                title="启动失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return

        self.current_task_id = task_id
        self.current_task_name = task.name
        self._process_gone_at = None
        self._capture_dead_reported = False
        self.home_page.set_running(True, task.name, task_id)
        self._log(f"已启动任务: {task.name}  参数: {kwargs}", "info")
        InfoBar.success(
            title="任务已启动",
            content=task.name,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def _stop_task(self):
        if self.runner.is_running:
            self.runner.stop()
            self._log(f"已停止任务: {self.current_task_name}", "warning")
            InfoBar.warning(
                title="任务已停止",
                content=self.current_task_name,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        # 进程已经没了、界面却还显示「运行中」时（漏了「done」）也要把状态收回来
        self._process_gone_at = None
        self._capture_dead_reported = False
        self.home_page.set_running(False)
        self.current_task_id = None

    # ------------------------------------------------------------------
    # 原神登录全局快捷键（先按 g 再按数字）
    # ------------------------------------------------------------------
    def _setup_login_hotkeys(self):
        """装全局键盘钩子，注册 <前缀>+1 ~ <前缀>+9（默认 +1 ~ +9）。

        刷本 / 登录时焦点都在游戏窗口上，Qt 的 QShortcut 只在程序窗口激活时
        才触发，所以这里用 pynput 装**全局**钩子（和 ys_talk 的 F10 开关同思路）。
        """
        try:
            from pynput import keyboard
        except Exception as e:
            self._log(f"未安装 pynput，全局登录快捷键不可用: {e}", "error")
            return
        try:
            self._hotkey_listener = keyboard.Listener(on_press=self._on_global_key)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
        except Exception as e:
            self._log(f"注册全局登录快捷键失败: {e}", "error")
            return
        self._log(
            f"全局快捷键已就绪：{self.快捷键前缀}+1~9 登录第 1~9 个账号，"
            f"{self.快捷键前缀}+{self.剧情快捷键} 开/关原神自动剧情"
            f"（焦点在游戏窗口也生效）",
            "info",
        )

    def _on_global_key(self, key):
        """全局按键回调。

        ⚠ 这里跑在 pynput 的监听线程里，**不能直接操作界面**，
        所以只做最轻量的判断，然后把数字通过信号丢给 Qt 主线程。
        """
        char = getattr(key, "char", None)
        if not char:
            return                      # 功能键（shift/ctrl 等）没有 char
        now = time.time()

        if char.lower() == self.快捷键前缀.lower():
            self._hotkey_pending = now
            return
        # 前缀之后：数字 -> 登录对应账号；剧情键 -> 开/关自动剧情
        digit_char = char if char.isdigit() else self._上档数字.get(char)
        is_talk = char.lower() == self.剧情快捷键.lower()
        if digit_char or is_talk:
            pending = self._hotkey_pending
            self._hotkey_pending = None
            if pending is None or now - pending > self.快捷键间隔:
                return
            if digit_char:
                self.loginHotkeyPressed.emit(int(digit_char))
            else:
                self.talkHotkeyPressed.emit()
            return
        self._hotkey_pending = None     # 按了别的键就取消本次组合

    def _login_account(self, digit):
        """快捷键 <前缀>+digit -> 登录第 digit 个原神账号（序号 digit-1）。

        账号不足 digit 个时**不执行**，只给一条提示。
        """
        # 任务运行中一律忽略：自动化会用 keyboard.write 输入账号/兑换码
        # （例如 "kechengzhuang524@126.com" 里就夹着字母和数字），
        # 全局钩子能收到这些模拟按键，不挡掉就可能误触发登录。
        if self.runner.is_running:
            return

        # 在本窗口的输入框里打字时不要抢按键（仅当本窗口激活时判断，
        # 否则焦点在游戏上时会误判成“正在输入框里”）
        if self.isActiveWindow() and isinstance(
            QApplication.focusWidget(), QLineEdit
        ):
            return

        # 切到原神页，保证用户能看到被选中的卡片
        self.home_page.show_game("原神")
        card = self.home_page.card_for("ys_login_one")
        if card is None:
            return
        combo = card.param_widgets.get("n")
        index = digit - 1
        count = combo.count() if combo is not None else 0

        if index >= count:
            self._log(
                f"快捷键 {self.快捷键前缀}{digit}: "
                f"原神账号不足 {digit} 个（当前 {count} 个），不执行",
                "warning",
            )
            InfoBar.warning(
                title="没有这个账号",
                content=f"{self.快捷键前缀}{digit} 需要第 {digit} 个原神账号，"
                        f"当前只有 {count} 个",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return

        combo.setCurrentIndex(index)
        card.radio.setChecked(True)     # 让卡片选中态与实际执行的一致
        account = combo.currentText()
        self._log(
            f"快捷键 {self.快捷键前缀}{digit}: 登录原神账号 {index} - {account}",
            "info",
        )
        self._start_task(card.task.id, card.param_values())

    def _toggle_talk(self):
        """快捷键 <前缀>+t -> 开/关原神自动剧情。

        剧情是「开关型」任务：没跑就打开，正在跑就关掉。
        顺带避免任务运行中输入文字时把 t 误当成快捷键。
        """
        self.home_page.show_game("原神")       # 切回原神页，让开关可见
        if self.home_page.switch_for("ys_talk") is None:
            return

        if self.runner.is_running:
            # 只有在跑的**就是这个**剧情任务时才响应关闭；
            # 跑的是别的任务就忽略，避免自动化输入文字时误触发
            if self.current_task_id == "ys_talk":
                self._log("快捷键: 关闭原神自动剧情", "info")
                self._stop_task()
            return

        self._log("快捷键: 开启原神自动剧情", "info")
        self._start_task("ys_talk", {})

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def _log(self, message, level="info"):
        self.log_page.append(message, level)

    def _poll_queue(self):
        while not self.log_queue.empty():
            try:
                kind, level, message = self.log_queue.get_nowait()
            except Exception:
                break
            if kind == "log":
                self._log(message, level)
            elif kind == "done":
                # 自动重开时旧进程可能残留一条「done」，别把新进程的状态带偏
                if time.time() < self._restart_guard_until:
                    continue
                if self.current_task_id is None:
                    continue            # 已经收过尾了（见下面的「进程已退出」兜底）
                self._process_gone_at = None
                self.current_task_id = None
                self.home_page.set_running(False)
                self._log(f"任务结束: {message}", level)
            elif kind == "capture_dead":
                # 截图线程自己已经「杀掉重开」过好几次（见 func.screenshot 的
                # 看门狗），还是没有画面：多半是窗口被遮挡/最小化/显示器关了。
                # 默认只提醒用户，不擅自杀任务进程（见 AUTO_RESTART_ON_CAPTURE_DEAD）。
                if AUTO_RESTART_ON_CAPTURE_DEAD:
                    self._auto_restart_task(message)
                else:
                    self._report_capture_dead(message)

        # 兜底：进程已经没了却没收到（或漏了）「done」——别让界面一直显示「运行中」。
        # 先等 3 秒：正常结束时「done」可能还在队列管道里没读出来，别误报成异常退出。
        if (self.current_task_id is not None and not self.runner.is_running
                and time.time() >= self._restart_guard_until):
            if self._process_gone_at is None:
                self._process_gone_at = time.time()
            elif time.time() - self._process_gone_at >= 3.0:
                self._process_gone_at = None
                self.current_task_id = None
                self.home_page.set_running(False)
                self._log("任务进程已退出（没有收到结束消息）", "warning")
        else:
            self._process_gone_at = None

    def _report_capture_dead(self, reason):
        """截图彻底抓不到画面：只报警，不动任务进程（默认行为）。

        截图线程的看门狗（``func.screenshot``）已经尽力了：连续失败 10 次（≈10 秒）
        或卡在系统调用里都会**杀掉旧线程重新拉起**。到这个地步还没有画面，基本只剩
        两种可能：窗口被别的窗口整个盖住 / 最小化（全屏游戏此时根本抓不到），或者
        显示器关了 / 会话锁了。这两种只能由用户处理（把游戏切回前台，或改成窗口化
        模式），所以这里只提示一次，不杀任务、不抢焦点。
        """
        if self._capture_dead_reported:
            return
        self._capture_dead_reported = True
        hint = ("把游戏窗口切回前台（或把崩铁/原神改成「窗口化」模式）后会自动恢复；"
                "截图线程已经自动杀过并重开多次，仍然没画面说明窗口被挡住/最小化，"
                "或者显示器已关闭 / 会话已锁屏")
        self._log(f"截图一直抓不到画面：{reason}", "error")
        self._log(hint, "warning")
        InfoBar.error(
            title="截图停止更新",
            content=hint,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self,
        )

    def _auto_restart_task(self, reason):
        """截图彻底救不回来 -> 收掉整棵任务进程树，按原参数重新拉起。

        **默认不会走到这里**（见 ``AUTO_RESTART_ON_CAPTURE_DEAD``）：重开进程会把
        任务脚本自己起的点击子进程一起收掉，重开时还会把游戏窗口抢回前台，正在用
        电脑的人会被打断。打开开关后才启用这条更强的兜底。

        这里必须走 ``TaskRunner.restart``（先 ``_kill_tree`` 再起新进程），否则任务
        脚本自己起的点击子进程会变成孤儿，继续对着游戏乱点。
        """
        self._log(f"截图救不回来了: {reason}", "error")
        if self.current_task_id is None or not self.runner.is_running:
            return
        if not self.runner.can_restart:
            self._log(
                "自动重开任务次数已用完，停止任务；请检查游戏窗口是否被遮挡/最小化、"
                "显示器是否关闭或已锁屏", "error")
            self._stop_task()
            return
        self._restart_guard_until = time.time() + 1.0
        try:
            self.runner.restart()
        except Exception as e:
            self._log(f"自动重开任务失败: {e}", "error")
            self._stop_task()
            return
        self._log(
            f"已自动重开任务进程（第 {self.runner.restart_count} 次）: "
            f"{self.current_task_name}", "warning")
        InfoBar.warning(
            title="已自动重开任务",
            content=f"截图连续抓不到画面，已重新拉起: {self.current_task_name}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self,
        )

    def _toggle_theme(self):
        app = QApplication.instance()
        current = app.styleSheet()
        # 简单在浅色/深色间切换
        if getattr(self, "_dark", False):
            setTheme(Theme.LIGHT)
            self._dark = False
        else:
            setTheme(Theme.DARK)
            self._dark = True

    def closeEvent(self, event):
        if self.runner.is_running:
            self.runner.stop()
        # 卸掉全局键盘钩子
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None
        super().closeEvent(event)
