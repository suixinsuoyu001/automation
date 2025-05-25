import threading

from func.common import *
from func.get_pic import get_pic
from func.match.template_match import t_match
from func.control.back_control import Control

windows_title = '崩坏：星穹铁道'
# os.startfile(open_game(game_name))
# get_pic(game_name)
hwnd = get_hwnd(windows_title)
control = Control(hwnd)

current_dir = os.path.dirname(os.path.abspath(__file__))



class check():
    def __init__(self,windows_title,num = 0.9,time_limit = 0):
        self.wt = windows_title
        self.time_limit = time_limit
        self.num = num
        self.hwnd = get_hwnd(windows_title)
        path = current_dir.replace('action','image\\')
        json_path = current_dir.replace('action','data\img_loc.json')
        self.path = path
        self.json_path = json_path
        self.t_match = t_match(windows_title, path)
        self.locs = read_json(json_path)
        self.processed_screen = None

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

    def check_start(self):
        self.stop_event = threading.Event()
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
        self.thread = threading.Thread(target=self.get_pic_loop)
        self.thread.start()
        time.sleep(1)
        control.activate()
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

    def match_one_pic(self,name):
        return self.t_match.match_pic(name,num,self.processed_screen)

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
        image = self.processed_screen
        template = load_image_with_zh_path(f'{self.path}{name}.png')
        result = self.t_match.get_match_result(image, template)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 设置一个阈值来过滤低相关度的匹配
        threshold = num
        log(max_val)
        if max_val >= threshold:
            # 计算模板匹配的区域坐标
            top_left = list(max_loc)
            h, w, channels = template.shape  # 模板的高度和宽度
            bottom_right = [top_left[0] + w, top_left[1] + h]
            locs = read_json(self.json_path)
            locs[name] = locs.get(name, [])
            if [top_left, bottom_right] not in locs[name]:
                locs[name].append([top_left, bottom_right])
            save_json(self.json_path, locs)
        else:
            log("匹配失败")

    def wait_click(self,name,num = None):
        num = self.num if num is None else num
        if self.processed_screen is None:
            log('check_start未运行')
            return
        log(f'wait_click:{name} 开始捕获')
        flag = 0
        while True:
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                control.activate()
                control.click(position[0])
                control.inactivate()
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                break
            time.sleep(0.02)
        log(f'wait_click:{name} 已捕获并点击')

    def click_until(self,name,item_names,num = None):
        num = self.num if num is None else num
        log(f'click_loop_until: 开始循环遍历 {names}')
        while True:
            for name in item_names + names:
                position = self.check_one_pic(name,num,self.processed_screen)
                if position:
                    if name in names:
                        control.click(position[0])
                        log(f'click_loop_until: 点击 {name}')
                        time.sleep(0.5)
                    else:
                        log(f'click_loop_until: {name} 已捕获 结束循环')
                        return name

if __name__ == '__main__':
    c = check(windows_title)
    c.check_start()
    # # c.save_pic_loc('点击进入')
    c.show_pic()

