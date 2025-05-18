import os
import time

import pyautogui
import numpy as np
from PIL import Image
import cv2


class match():
    def __init__(self,path,num):
        self.path = path
        self.num = num

    def load_image_with_chinese_path(self,path):
        pil_img = Image.open(path).convert('RGB')
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def find_image_on_screen(self,name, threshold=0.8):
        template_path =  f"{self.path}{name}.png"
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"文件不存在: {os.path.abspath(template_path)}")
        try:
            template = self.load_image_with_chinese_path(template_path)
        except Exception as e:
            raise ValueError(f"读取图片失败: {e}")
        h, w = template.shape[:2]
        screenshot = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_cv = cv2.resize(screenshot_cv, (2560, 1440), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        yloc, xloc = np.where(result >= threshold)
        rectangles = []
        for (x, y) in zip(xloc, yloc):
            rectangles.append([int(x), int(y), int(w), int(h)])
            rectangles.append([int(x), int(y), int(w), int(h)])  # 为 groupRectangles 提供两次重复输入

        rectangles, _ = cv2.groupRectangles(rectangles, groupThreshold=1, eps=0.5)
        centers = []
        for (x, y, w, h) in rectangles:
            centers.append((int(x + w // 2), int(y + h // 2)))

        return centers

    def click(self,name,num = None):
        print(f'click:{name} 开始捕获')
        if num is None:
            num = self.num
        while True:
            matches = self.find_image_on_screen(name,num)
            if matches:
                pyautogui.click(matches[0])
                print(f'click:{name} 已捕获并点击')
                break

    def wait(self,name,num = None):
        if num is None:
            num = self.num
        while True:
            matches = self.find_image_on_screen(name,num)
            if matches:
                break

    def waits(self,names, num=None):
        if num is None:
            num = self.num
        while True:
            for name in names:
                matches = self.find_image_on_screen(name,num)
                if matches:
                    time.sleep(0.2)
                    return name

    def click_num(self,name,n):
        while True:
            matches = self.find_image_on_screen(name)
            if matches:
                pyautogui.click(matches[n])
                break


if __name__ == '__main__':
    time.sleep(2)
    path = 'E:\python\pythonAuto\games/mc/image/'
    g_match = match(path,0.9)

    g_match.click('账号标识')