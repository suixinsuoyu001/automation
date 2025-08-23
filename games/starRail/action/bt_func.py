import threading
import pyautogui
import win32con
from PIL import Image
from func.common import *
from func.get_pic import get_pic
from func.match.template_match import t_match
from func.control.back_control import Control

windows_title = '崩坏：星穹铁道'


current_dir = os.path.dirname(os.path.abspath(__file__))

zhs = [
    'suixin001007@163.com', #0
    'suixin001006@163.com', #1
    'suixin001009@163.com', #2
    'suixin001001@163.com', #3
    '13280859317',          #4
    'suixin001002@163.com', #5
    'suixin001005@163.com', #6
    'suixin001003@163.com', #7
    'suixin001004@163.com', #8
    'suixin001008@163.com', #9
]

class check():
    def __init__(self,windows_title,num = 0.8,time_limit = 0):
        self.wt = windows_title
        self.time_limit = time_limit
        self.num = num
        self.hwnd = get_hwnd(windows_title)
        self.control = Control(self.hwnd)
        image_path = current_dir.replace('action','image\\')
        json_path = current_dir.replace('action','data\img_loc.json')
        self.path = image_path
        self.json_path = json_path
        self.t_match = t_match(self.wt, self.path)
        self.locs = read_json(json_path)
        self.processed_screen = None
        self.focus = False
        self.zhs = zhs

    def is_focus(self):
        focus = get_focus_window()
        if focus and windows_title in focus:
            return True
        return False

    def get_pic_loop(self):
        while True:
            time.sleep(self.time_limit)
            if self.stop_event.is_set():  # 当 e 事件被 set 时，退出循环
                break
            try:
                pic = get_pic(self.wt)
            except:
                pic = None
                log('图片获取失败')
            if pic is not None:
                self.processed_screen = get_pic(self.wt)
                self.focus = self.is_focus()
            else:
                while not get_hwnd(self.wt):
                    log(f'等待{self.wt}启动')
                    time.sleep(5)
                self.hwnd = get_hwnd(self.wt)
                self.control = Control(self.hwnd)
    def check_start(self):
        self.stop_event = threading.Event()
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
        self.hwnd = get_hwnd(self.wt)
        self.t_match = t_match(self.wt, self.path)
        self.control = Control(self.hwnd)
        self.thread = threading.Thread(target=self.get_pic_loop)
        self.thread.start()
        time.sleep(1)
        log("获取图片进程已开始")

    def check_stop(self):
        self.stop_event.set()  # 触发停止事件
        self.thread.join()  # 等待线程结束
        log("获取图片进程已停止")

    def show_pic(self):
        window_name = "Processed Screen"
        while True:
            t0 = time.time()
            processed_screen = self.processed_screen
            processed_screen = reset_pic(processed_screen, 1600, 900)
            cv2.imshow(window_name, processed_screen)
            # set_window_topmost(window_name)  # 设置窗口置顶
            # 退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # log(f'总用时 {time.time() - t0}')

        cv2.destroyAllWindows()

    def match_one_pic(self,name,num):
        return self.t_match.match_pic(name,num,self.processed_screen)

    def match_pics(self,name,num):
        return self.t_match.match_pics(name,num,self.processed_screen)

    def check_one_pic(self,name,num,screen):
        if screen is None:
            return
        if self.locs.get(name) is None:
            return self.match_one_pic(name, num)
        for point in self.locs[name]:
            p1, p2 = point
            x, y, w, h = p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1]
            new_screen = screen[y:y + h, x:x + w]  # 裁剪图像
            point = [(p1[0]+p2[0])//2, (p1[1]+p2[1])//2]
            res = self.t_match.match_pic(name,num,new_screen)
            if res:
                max_val, max_loc = res
                return [point,max_val]

    def save_pic_loc(self,name,num = None):
        num = self.num if num is None else num
        image = get_pic(self.wt)
        template = load_image_with_zh_path(f'{self.path}{name}.png')
        result = self.t_match.get_match_result(image, template)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        h, w, channels = template.shape  # 模板的高度和宽度
        x,y = max_loc
        cropped_img = image[y:y+h, x:x+w]

        output_file = "item.png"
        # cv2.imwrite(output_file, cropped_img)
        # 设置一个阈值来过滤低相关度的匹配
        threshold = num
        log(max_val,max_loc)
        if max_val >= threshold:
            # 计算模板匹配的区域坐标
            top_left = list(max_loc)
            bottom_right = [top_left[0] + w, top_left[1] + h]
            locs = read_json(self.json_path)
            locs[name] = locs.get(name, [])
            if [top_left, bottom_right] not in locs[name]:
                locs[name].append([top_left, bottom_right])
            save_json(self.json_path, locs)
        else:
            log("匹配失败")

    def post(self,func, a1=None, a2=None):
        self.control.block_user_input()
        self.control.activate()
        time.sleep(0.01)
        x, y = self.control.get_mouse_position()
        time.sleep(0.01)
        if a2:
            func(a1, a2)
        elif a1:
            func(a1)
        else:
            func()
        time.sleep(0.02)
        self.control.inactivate()
        time.sleep(0.03)
        self.control.set_mouse_position(x, y)
        self.control.unblock_user_input()
        if self.focus:
            self.control.activate()


    def click(self,name,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        log(f'click:{name} 开始捕获',level=2)
        while True:
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.post(self.control.click, get_position(position[0]))
                break
            time.sleep(0.02)
        log(f'click:{name} 已捕获并点击',level=2)

    def click_speed(self,name,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
        position = self.check_one_pic(name, num, self.processed_screen)
        if position is not None:
            self.post(self.control.click, get_position(position[0]))
        log(f'click_speed:{name} 已捕获并点击',level=2)

    def click_point(self,point):
        self.post(self.control.click, point)
        log(f'click:{point} 已点击',level=2)

    def wait_click(self,name,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        log(f'wait_click:{name} 开始捕获',level=2)
        flag = 0
        while True:
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.post(self.control.click, get_position(position[0]))
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                break
            time.sleep(0.02)
        log(f'wait_click:{name} 已捕获并点击',level=2)

    def wait_click_limit(self,name,t = 2,num = 0.9):
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        log(f'wait_click_limit:{name} 开始捕获',level=2)
        flag = 0
        start_time = time.time()
        while True:
            if not self.focus:
                self.control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.post(self.control.click,get_position(position[0]))
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                log(f'wait_click_limit:{name} 已捕获并点击',level=2)
                break
            time.sleep(0.02)
            if time.time() - start_time > t:
                log(f'wait_click_limit:{name} 未捕获，超时取消',level=2)
                break

    def click_until(self,name,item_name,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        log(f'click_until:{name} 开始捕获',level=2)
        while True:
            position = self.check_one_pic(name, num, self.processed_screen)
            item_position = self.check_one_pic(item_name, num, self.processed_screen)
            if item_position:
                log(f'click_until:{item_position} 已识别结束循环',level=2)
                break
            if position is not None:
                self.post(self.control.click,get_position(position[0]))
                log(f'click_until:{name} 已捕获并点击',level=2)
                time.sleep(1)
            time.sleep(0.02)

    def send_key(self,key):
        log(f'send_key: 按下 {key}',level=2)
        self.post(self.control.send_key_up, key)

    def waits(self,names,num = None):
        num = self.num if num is None else num
        log(f'waits:{names} 开始捕获',level=2)
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            self.hwnd = get_hwnd(windows_title)
            # return
        while True:
            for name in names:
                position = self.check_one_pic(name,num,self.processed_screen)
                if position:
                    log(f'waits: {name} 已找到',level=2)
                    time.sleep(0.5)
                    return name

    def waits_limit(self,names,t = 2,num = None):
        num = self.num if num is None else num
        log(f'waits_limit:{names} 开始捕获',level=2)
        start_time = time.time()
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        while True:
            for name in names:
                position = self.check_one_pic(name,num,self.processed_screen)
                if position:
                    log(f'waits: {name} 已找到',level=2)
                    time.sleep(0.5)
                    return name
                if time.time() - start_time > t:
                    log(f'waits_limit:{name} 未捕获，超时取消',level=2)
                    return None

    def waits_speed(self,names,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
        for name in names:
            position = self.check_one_pic(name,num,self.processed_screen)
            if position:
                return name

    def text_input(self,name,text,num = None):
        num = self.num if num is None else num
        log(f'text_input:{name} 开始捕获录入',level=2)
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        while True:
            position = self.check_one_pic(name,num,self.processed_screen)
            if position:
                log(f'text_input: {name} 已找到开始点击输入',level=2)
                self.post(self.control.click_input, get_position(position[0]),text)
                return name

    def hold_click(self,point):
        self.control.block_user_input()
        if not self.focus:
            self.control.activate()
        log(f'hold_click: 点击坐标{point}',level=2)

        x, y = self.control.get_mouse_position()
        time.sleep(0.02)
        self.control.send_key_down('alt')
        time.sleep(0.01)
        ctypes.windll.user32.SetCursorPos(point[0],point[1])
        if self.control.get_mouse_position() == point:
            self.control.click(point)
            self.control.send_key_up('alt')
            time.sleep(0.02)
            if not self.focus:
                self.control.inactivate()
            time.sleep(0.02)
            self.control.set_mouse_position(x, y)
        else:
            time.sleep(0.5)
            self.hold_click(point)
        self.control.unblock_user_input()



    def move_click(self,sign,item,num = None):
        num = self.num if num is None else num
        log(f'move_scroll:{sign} 开始捕获',level=2)
        while True:
            position = self.check_one_pic(sign, num, self.processed_screen)
            if position is None:
                time.sleep(0.02)
                continue
            while True:
                position2 = self.check_one_pic(item, num, self.processed_screen)
                if position2:
                    self.post(self.control.click, get_position(position2[0]))
                    break
                self.post(self.control.move_scroll, get_position(position[0]),150)

            break
        log(f'click:{sign} 已捕获并点击',level=2)

    def move_wait(self,sign,item,num = None):
        num = self.num if num is None else num
        log(f'move_scroll:{sign} 开始捕获',level=2)
        while True:
            position = self.check_one_pic(sign, num, self.processed_screen)
            if position is None:
                time.sleep(0.02)
                continue
            while True:
                position2 = self.check_one_pic(item, 0.95, self.processed_screen)
                if position2:
                    break
                self.post(self.control.move_scroll, get_position(position[0]),150)

            break
        log(f'click:{sign} 已捕获并点击')

    def click_move_item(self,sign,item,num = None):
        num = self.num if num is None else num
        log(f'move_scroll:{sign} 开始捕获',level=2)
        while True:
            position = self.check_one_pic(sign, num, self.processed_screen)
            if position is None:
                time.sleep(0.02)
                continue
            while True:
                matches = self.match_pics(item, num)
                if not matches:
                    continue
                y = position[0][1]
                for i in matches:
                    if i['y'] > y-100:
                        self.post(self.control.click,get_position([i['x'],i['y']]))
                        break
                break

            break
        log(f'click:{sign} 已捕获并点击',level=2)

if __name__ == '__main__':
    # game_start(windows_title)
    c = check(windows_title)
    # c.save_pic_loc('空白位置',0.8)


    c.check_start()
    # c.move_click('拟造花萼金','侵蚀隧洞')
    # c.move_wait('侵蚀隧洞标识', '遗器副本1')

    # c.check_start()
    # c.waits(['test'])
    while True:
        c.wait_click('再来一次')
        time.sleep(3)
    #
    # # c.send_key('esc')
    # # time.sleep(0.5)
    # # c.send_key('esc')
    #
    #
    # # c.waits(['Enter'])
    # # c.send_key('b')
    # # c.click_until(c.waits(['遗器1', '遗器2']), '分解')
    # # c.wait_click('分解')
    #
    #
    c.check_stop()
