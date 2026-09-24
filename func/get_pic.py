"""截图模块（兼容层）。

真正的实现已迁移到 :mod:`func.screenshot` 的**通用循环截图服务**：

* 循环截图只跑一个后台线程（``func.screenshot.service``）；
* 原神 / 崩铁 / 鸣潮所有功能共享同一份最新画面；
* ``get_pic(window_title)`` 签名保持不变——服务已启动时直接返回共享帧
  （零拷贝），未启动时回退为单次实时截图。

这里用 ``import *`` 重新导出，是为了让 ``from func.get_pic import *``
拿到和以前完全一样的名字（``get_pic`` / ``get_hwnd`` / ``log`` /
``setting`` / ``cv2`` / ``np`` / ``time`` ...），老代码无需改动。
"""

from func.common import get_hwnd, log, setting
from func.screenshot import *          # noqa: F401,F403  (保持原有星号导入表面)
from func.screenshot import (          # 显式列出，便于 IDE 与静态检查
    DEFAULT_INTERVAL,
    ScreenshotService,
    capture_hwnd,
    capture_window,
    get_pic,
    is_capturing,
    latest,
    service,
    set_capture_interval,
    start_capture,
    stop_capture,
    wait_first_frame,
)


if __name__ == '__main__':
    import time as _time

    t = _time.time()
    # 使用窗口标题调用
    get_pic("原神")
    # get_pic("鸣潮  ")
    # get_pic("崩坏：星穹铁道")
    print(_time.time() - t)


