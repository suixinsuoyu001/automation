"""任务执行器。

在独立子进程中运行自动化任务，避免阻塞 UI 线程，并支持强制停止。
任务函数通过字符串路径延迟导入，保证子进程内能正确加载项目模块。

为什么不能用 daemon=True
------------------------
``ys_talk`` / ``bt_talk`` / ``bt_auto`` / ``bt_mnyz`` / ``mc_jq`` / ``mc_hd``
这些脚本内部还会再用 ``multiprocessing.Process`` 起一个"点击循环"进程
（``start_node()``）。而 Python 规定**守护进程不允许创建子进程**，一旦用
``daemon=True`` 就会立刻抛：

    AssertionError: daemonic processes are not allowed to have children

任务看起来"启动了"但什么都没做。所以这里必须 ``daemon=False``。
代价是父进程被杀时子进程不会自动回收，需要在 :meth:`TaskRunner.stop`
里显式结束整棵进程树，否则遗留的点击进程会继续操作游戏。
"""
import multiprocessing
import os
import sys
import time
import traceback

# 保证子进程能 import 到项目根目录下的 games / func 等模块
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------------------------
# 「截图彻底救不回来就重开任务进程」的阈值
# ---------------------------------------------------------------------------
# 画面连续这么久没有**任何**新帧（截图线程自己已经重启过也不行），就认为不是
# 线程的问题，而是进程级的 GDI / DWM 状态坏了 —— 只有重开进程能救。
# 3 分钟是个保守值：正常加载/过场/切场景都不会这么久抓不到画面。
CAPTURE_DEAD_SECONDS = 180.0

# 子进程里多久检查一次截图健康度（秒）
CAPTURE_MONITOR_INTERVAL = 5.0

# 同一个任务进程最多报告几次「截图救不回来了」（界面每次收到都会重开进程）
CAPTURE_NOTIFY_LIMIT = 3


def _resolve(path):
    """根据 'module:attr' 或 'module.attr' 字符串解析出可调用对象。"""
    if ":" in path:
        module_name, attr = path.split(":", 1)
    else:
        module_name, attr = path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[attr])
    return getattr(module, attr)


def _capture_monitor(log_queue):
    """盯着循环截图服务的健康度：画面彻底不更新就报告给界面。

    为什么不在子进程里自己 ``os._exit``：任务脚本自己还会用 multiprocessing
    起「点击循环」子进程，父进程被直接干掉的话那些子进程会变成孤儿，继续对着
    游戏乱点。所以这里**只报告**；界面默认只把它转成「日志 + 提示」（重开进程
    要显式打开 ``main_window.AUTO_RESTART_ON_CAPTURE_DEAD``），需要时再用
    :meth:`TaskRunner.restart` 收掉整棵进程树、按原参数重新拉起。

    报告条件（两个都满足才会报告）：
      * 截图服务认为画面已陈旧（连续失败，调用方已停止用旧画面做判断）
      * 连续 ``CAPTURE_DEAD_SECONDS`` 秒没有抓到**任何**一帧
        （截图线程自己已经被看门狗「杀掉重开」过几次也没用）
    """
    try:
        from func import screenshot
    except Exception:
        return
    reported = 0
    while True:
        time.sleep(CAPTURE_MONITOR_INTERVAL)
        try:
            if not screenshot.is_capturing():
                continue            # 还没开始截图 / 已经停了：不归我们管
            svc = screenshot.service
            age = svc.last_frame_age
            if not svc.stale or age < CAPTURE_DEAD_SECONDS:
                continue
            if reported >= CAPTURE_NOTIFY_LIMIT:
                continue
            reported += 1
            msg = (f'画面已经 {age:.0f}s 没有更新（连续失败 {svc.fail_count} 次，'
                   f'截图线程已被杀掉重开 {svc.restart_count} 次），'
                   f'请检查游戏窗口是否被遮挡/最小化、显示器是否关闭')
            print(msg, flush=True)
            try:
                log_queue.put(("capture_dead", "error", msg))
            except Exception:
                pass
        except Exception:
            pass


def _worker(task_path, kwargs, log_queue):
    """子进程入口：执行任务并把日志/状态写回队列。"""
    # 子进程内重新设置工作目录与路径
    os.chdir(ROOT_DIR)
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

    def emit(msg, level="info"):
        print(msg, flush=True)
        try:
            log_queue.put(("log", level, str(msg)))
        except Exception:
            pass

    # 截图健康度监控：画面彻底死掉时通知界面重开任务进程（见 _capture_monitor）
    try:
        import threading

        threading.Thread(
            target=_capture_monitor, args=(log_queue,),
            name='CaptureHealthMonitor', daemon=True,
        ).start()
    except Exception:
        pass

    try:
        emit(f"开始执行任务: {task_path}")
        func = _resolve(task_path)
        func(**kwargs)
        emit("任务执行完成", "success")
        log_queue.put(("done", "success", "任务执行完成"))
    except Exception as e:
        tb = traceback.format_exc()
        emit(f"任务执行异常: {e}\n{tb}", "error")
        try:
            log_queue.put(("done", "error", str(e)))
        except Exception:
            pass
    finally:
        # 收尾：停掉通用循环截图线程，避免残留后台线程
        try:
            from func import screenshot

            screenshot.stop_capture()
        except Exception:
            pass
        try:
            log_queue.close()
        except Exception:
            pass


def _kill_tree(pid, timeout=5):
    """结束 pid 及其所有子孙进程。

    任务脚本自己会用 multiprocessing 起子进程，单纯 terminate 父进程会
    留下孤儿进程继续点击游戏，所以这里按整棵树回收。
    """
    try:
        import psutil
    except ImportError:
        return
    try:
        parent = psutil.Process(pid)
        procs = parent.children(recursive=True)
    except Exception:
        return
    procs.append(parent)
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    _, alive = psutil.wait_procs(procs, timeout=timeout)
    for p in alive:
        try:
            p.kill()
        except Exception:
            pass
    if alive:
        psutil.wait_procs(alive, timeout=2)


class TaskRunner:
    """管理单个后台任务进程。"""

    # 同一个任务最多自动重开几次（截图彻底救不回来时用，见 TaskRunner.restart）
    MAX_RESTARTS = 2

    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.process = None
        # 上一次启动用的入口和参数：自动重开时原样复用（见 restart）
        self.last_entry = None
        self.last_kwargs = {}
        self.restart_count = 0

    @property
    def is_running(self):
        return self.process is not None and self.process.is_alive()

    @property
    def exit_code(self):
        """上一次结束的任务进程的退出码（没起过/还在跑时为 None）。"""
        return None if self.process is None else self.process.exitcode

    @property
    def can_restart(self):
        """还能不能自动重开（有上次的入口、且没超过次数上限）。"""
        return self.last_entry is not None and self.restart_count < self.MAX_RESTARTS

    def start(self, task_path, kwargs=None):
        if self.is_running:
            raise RuntimeError("已有任务正在运行")
        self.restart_count = 0
        return self._spawn(task_path, kwargs or {})

    def restart(self):
        """按上次的任务入口和参数**重新拉起**任务进程。

        用于「截图彻底救不回来」的自动恢复：先把整棵进程树收掉（含任务脚本
        自己起的点击循环子进程，不然它们会变成孤儿继续点游戏），再起一个新的
        任务进程，参数和刚才完全一致。

        :return: 新进程 pid
        :raises RuntimeError: 没有上次的任务入口，或者自动重启次数已用完
        """
        if not self.can_restart:
            raise RuntimeError("没有可重启的任务，或自动重启次数已用完")
        entry, kwargs = self.last_entry, dict(self.last_kwargs)
        self.stop()                 # 收掉整棵进程树
        self.restart_count += 1
        return self._spawn(entry, kwargs)

    def _spawn(self, task_path, kwargs):
        self.last_entry = task_path
        self.last_kwargs = dict(kwargs or {})
        self.process = multiprocessing.Process(
            target=_worker,
            args=(task_path, self.last_kwargs, self.log_queue),
            # 必须是 False：任务脚本内部还要再起子进程（见模块文档）
            daemon=False,
        )
        self.process.start()
        return self.process.pid

    def stop(self, timeout=5):
        if self.process is None:
            return
        process = self.process
        self.process = None

        # 先收掉整棵进程树（含任务脚本自己起的点击循环进程）
        _kill_tree(process.pid, timeout)

        if process.is_alive():
            process.terminate()
            process.join(timeout)
        if process.is_alive():
            try:
                process.kill()
            except Exception:
                pass
            process.join(2)

        # 已强制回收，从 multiprocessing 的活跃列表里摘掉，
        # 否则解释器退出时的 atexit 还会去 join 它，导致关不掉窗口。
        try:
            import multiprocessing.process as mp_process

            if process in mp_process._children:
                mp_process._children.remove(process)
        except Exception:
            pass

