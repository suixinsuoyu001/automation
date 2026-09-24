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


def _resolve(path):
    """根据 'module:attr' 或 'module.attr' 字符串解析出可调用对象。"""
    if ":" in path:
        module_name, attr = path.split(":", 1)
    else:
        module_name, attr = path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[attr])
    return getattr(module, attr)


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

    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.process = None

    @property
    def is_running(self):
        return self.process is not None and self.process.is_alive()

    def start(self, task_path, kwargs=None):
        if self.is_running:
            raise RuntimeError("已有任务正在运行")
        kwargs = kwargs or {}
        self.process = multiprocessing.Process(
            target=_worker,
            args=(task_path, kwargs, self.log_queue),
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

