import pyautogui
import keyboard  # 用于监听键盘事件
import time

def listen_for_clicks():
    print("按下空格键获取当前鼠标位置，按 'esc' 键退出程序。\n")
    n = 0
    point1 = point2 = None
    while True:
        # 检查是否按下了空格键
        if keyboard.is_pressed('space'):  # 当按下空格键时
            n += 1
            # 获取当前鼠标位置
            x, y = pyautogui.position()
            if n == 1:
                point1 = (x, y)
            if n == 2:
                point2 = (x, y)
            print(f"当前鼠标坐标: ({x}, {y})")
            time.sleep(0.5)
        # 检查是否按下了 'esc' 键退出程序
        if keyboard.is_pressed('esc') or n == 2:
            print("\n程序退出")
            break
        time.sleep(0.2)
    return point1,point2


def get_percentage_position(coord1, coord2, screen_resolution):

    screen_width, screen_height = screen_resolution

    # 计算坐标1的百分比位置
    x1_percent = round((coord1[0] / screen_width) * 100,2)
    y1_percent = round((coord1[1] / screen_height) * 100,2)

    # 计算坐标2的百分比位置
    x2_percent = round((coord2[0] / screen_width) * 100,2)
    y2_percent = round((coord2[1] / screen_height) * 100,2)

    return (x1_percent, y1_percent), (x2_percent, y2_percent)

# 调用函数监听点击
point1,point2 = listen_for_clicks()
screen_resolution = (2560, 1440)  # 屏幕分辨率 (宽, 高)
print(point1,point2)
position_1, position_2 = get_percentage_position(point1, point2, screen_resolution)

print(f"position_1 = {position_1}")
print(f"position_2 = {position_2}")


