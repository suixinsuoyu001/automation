import time,win32gui,win32ui,cv2
from ctypes import windll
import numpy as np
from func.common import get_hwnd,log,setting


# def get_hwnd(target_title: str) -> str:
#     result = ""
#     def callback(hwnd, extra):
#         nonlocal result  # 让回调函数可以修改外部变量
#         if win32gui.IsWindowVisible(hwnd):  # 只查找可见窗口
#             title = win32gui.GetWindowText(hwnd)
#             if title and target_title == title:  # 模糊匹配
#                 result = hwnd
#
#     win32gui.EnumWindows(callback, None)
#     return result if result else None




def get_pic(window_title):
    """截取指定窗口的内容，去掉边框"""
    # 找到窗口句柄
    hwnd = get_hwnd(window_title)
    # print(hwnd)
    # hwnd = 4195764
    if not hwnd:
        log(f"Window with title '{window_title}' not found.",level=2)
        return None
    # try:
    windll.user32.SetProcessDPIAware()
    sp_left, sp_top, sp_right, sp_bot = win32gui.GetClientRect(hwnd)

    sp_w = sp_right - sp_left
    sp_h = sp_bot - sp_top
    real_sp_w = int(sp_w)
    real_sp_h = int(sp_h)
    hwndDC = win32gui.GetWindowDC(hwnd)  # 获取窗口设备上下文（DC）
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)  # 创建MFC DC从hwndDC
    saveDC = mfcDC.CreateCompatibleDC()  # 创建与mfcDC兼容的DC
    saveBitMap = win32ui.CreateBitmap()  # 创建一个位图对象
    # logger(f"int(real_sp_w), int(real_sp_h): {int(real_sp_w)}, {int(real_sp_h)}")
    saveBitMap.CreateCompatibleBitmap(
        mfcDC, int(real_sp_w), int(real_sp_h)
    )  # 创建与mfcDC兼容的位图
    saveDC.SelectObject(saveBitMap)  # 选择saveDC的位图对象，准备绘图
    # 尝试使用PrintWindow函数截取窗口图像
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
    if result != 1:
        return None  # 如果截取失败，则返回None
    # 从位图中获取图像数据
    bmp_info = saveBitMap.GetInfo()  # 获取位图信息
    bmp_str = saveBitMap.GetBitmapBits(True)  # 获取位图数据
    im = np.frombuffer(bmp_str, dtype="uint8")  # 将位图数据转换为numpy数组
    im.shape = (bmp_info["bmHeight"], bmp_info["bmWidth"], 4)  # 设置数组形状
    # im = im[:, :, [2, 1, 0, 3]][:, :, :3]  # 调整颜色通道顺序为RGB 并去掉alpha通道
    # im = im[:, :, [2, 1, 0]]  # 交换通道 BGR -> RGB
    im = im[:, :, :3]  # 保留 RGB 格式（不包括 alpha 通道）

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    if setting.get('resolution') != [2560, 1440]:
       im = cv2.resize(im, (2560, 1440), interpolation=cv2.INTER_AREA)
    output_file = "screenshot.png"
    # cv2.imwrite(output_file, im)
    # 1450, 657
    # 1795, 773

    return im  # 返回截取到的图像waA
    # except:
    #     log('获取截图失败')
    #     return None


if __name__ == '__main__':

    t = time.time()
    # 使用窗口标题调用
    get_pic("原神")
    # get_pic("鸣潮  ")
    # get_pic("崩坏：星穹铁道")
    print(time.time() -t)

