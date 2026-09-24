"""任务包装函数。

部分脚本没有可直接调用的入口（例如只有 start_node + 键盘监听），
这里提供统一的包装函数，供任务注册表引用。
"""


def bt_mnyz_run():
    """崩铁模拟宇宙：启动节点并监听键盘（按 B 键开关）。"""
    from games.starRail.execute import bt_mnyz

    bt_mnyz.start_node()
    try:
        from pynput import keyboard

        listener = keyboard.Listener(on_press=bt_mnyz.on_press)
        listener.start()
        listener.join()
    except Exception:
        # 无键盘监听环境时，退化为阻塞运行
        import time

        while True:
            time.sleep(1)
