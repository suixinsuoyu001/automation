from func.get_pic import *
from func.match.template_match import t_match
from func.common import *
from func.basic import *
import threading
from func.control.mc_control import *
from games.ys.match.yolo_match import *
from games.ys.action.ys_funtion import *

control = Control()

class check():
    def __init__(self,wt,path,json_path):
        self.wt = wt
        self.path = path
        self.t_match = t_match(wt, path)
        self.locs = read_json(json_path)
        self.processed_screen = None
        self.size_diff = None
        # self.check_game_state()

    # def check_game_state(self):
    #     log(f'等待{self.wt}启动',level=3)
    #     while not get_hwnd(self.wt):
    #         time.sleep(1)
    #     self.check_start()

    def get_pic_loop(self):
        while True:
            time.sleep(self.time_limit)  # 10ms 检测一次鼠标移动
            if self.stop_event.is_set():  # 当 e 事件被 set 时，退出循环
                break
            pic = get_pic(self.wt)
            try:
                pass
            except:
                pic = None
                log('图片获取失败')
            if pic is not None:
                self.processed_screen = get_pic(self.wt)

    def check_start(self,time_limit = 0.02):
        self.time_limit = time_limit
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


    def get_model_res_loop(self):
        # x1, y1 = get_position([200, 130])
        # x2, y2 = get_position([250, 190])
        x1, y1 = [200, 130]
        x2, y2 = [250, 190]
        while True:
            time.sleep(self.time_limit2)  # 10ms 检测一次鼠标移动
            if self.processed_screen is None:
                continue
            image = f"{self.path}朝向模板.png"
            cropped = self.processed_screen[y1:y2, x1:x2]
            self.ego_angle = match_ego_angle(image, cropped)

            match_res = model_match_pic(self.processed_screen)
            position_x = 2560 // 2
            if match_res:
                size = (match_res[0][0]+match_res[0][2])/2
                self.size_diff = size-position_x
            else:
                self.size_diff = None
            if self.stop_event2.is_set():  # 当 e 事件被 set 时，退出循环
                break

    def model_loop_start(self,time_limit = 0.1):
        self.time_limit2 = time_limit
        self.stop_event2 = threading.Event()
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
        self.thread2 = threading.Thread(target=self.get_model_res_loop)
        self.thread2.start()
        time.sleep(1)
        log("获取石化古树检出循环已开始")

    def model_loop_end(self):
        self.stop_event2.set()  # 触发停止事件
        self.thread2.join()  # 等待线程结束
        log("获取石化古树检出循环已停止")

    def func_loop(self, func):
        while True:
            func()
            time.sleep(self.time_limit_func)
            if self.stop_event_func.is_set():  # 当 e 事件被 set 时，退出循环
                break

    def func_loop_start(self,func,time_limit = 0.01):
        self.time_limit_func = time_limit
        self.stop_event_func = threading.Event()
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
        self.thread_func = threading.Thread(target=self.func_loop, args=(func,))
        self.thread_func.start()
        time.sleep(1)
        log(f"{func}循环已开始")

    def func_loop_end(self):
        self.stop_event_func.set()  # 触发停止事件
        self.thread_func.join()  # 等待线程结束
        log(f"循环已停止")

    def wait_loop(self, name):
        self.wait_flag = 0
        self.waits([name])
        self.wait_flag = 1

    def wait_loop_start(self,name):
        self.stop_event_wait = threading.Event()
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
        self.thread_wait = threading.Thread(target=self.wait_loop, args=(name,))
        self.thread_wait.start()
        time.sleep(1)
        log(f"wait_loop_start {name}循环已开始")


    def match_one_pic(self,name,num = 0.9):
        return self.t_match.match_pic(name,num,self.processed_screen)

    def match_pics(self,name,num = 0.9):
        return self.t_match.match_pics(name,num,self.processed_screen)

    def wait(self,name,num = 0.9):
        log(f'wait:{name} 开始捕获')
        while True:
            position = self.check_one_pic(name,num,self.processed_screen)
            if position:
                log(f'wait: {name} 已找到')
                time.sleep(0.5)
                return True


    def click(self,name,num = 0.9):
        if self.processed_screen is None:
            log('check_start未运行')
            self.check_start()
            # return
        log(f'click:{name} 开始捕获',level=2)
        while True:
            control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                control.click(position[0])
                time.sleep(0.5)
                break
            time.sleep(0.02)
        log(f'click:{name} 已捕获并点击',level=2)

    def wait_click(self,name,num = 0.9):
        if self.processed_screen is None:
            log('check_start未运行')
            return
        log(f'wait_click:{name} 开始捕获',level=2)
        flag = 0
        while True:
            control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                control.click(position[0])
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                break
            time.sleep(0.02)
        log(f'wait_click:{name} 已捕获并点击',level=2)

    def wait_click_limit(self,name,t,num = 0.9):
        if self.processed_screen is None:
            log('check_start未运行')
            return
        log(f'wait_click_limit:{name} 开始捕获',level=2)
        flag = 0
        start_time = time.time()
        while True:
            control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                control.click(position[0])
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                log(f'wait_click_limit:{name} 已捕获并点击',level=2)
                break
            time.sleep(0.02)
            if time.time() - start_time > t:
                log(f'wait_click_limit:{name} 未捕获，超时取消',level=2)
                break


    def wait_press(self,name,key,num = 0.9):
        log(f'wait_press:{name} 开始捕获',level=2)
        flag = 0
        while True:
            control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                control.send_key(key)
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                break
            time.sleep(0.02)
        log(f'wait_press:{name} 捕获 {key}已按下',level=2)

    def waits(self,names,num = 0.9):
        log(f'waits:{names} 开始捕获')
        if self.processed_screen is None:
            log('check_start未运行')
            return
        while True:
            for name in names:
                position = self.check_one_pic(name,num,self.processed_screen)
                if position:
                    log(f'wait: {name} 已找到')
                    time.sleep(0.5)
                    return name

    def waits_limit(self,names,t = 0.5,num = 0.9):
        log(f'waits_limit:{names} 开始捕获',level=2)
        if self.processed_screen is None:
            log('check_start未运行')
            return
        start_time = time.time()
        while True:
            for name in names:
                position = self.check_one_pic(name,num,self.processed_screen)
                if position:
                    log(f'wait: {name} 已找到')
                    time.sleep(0.1)
                    return name
            if time.time() - start_time > t:
                log(f'wait_limit:{names} 未捕获，超时取消',level=2)
                break

    def click_loop_until(self,names,item_names,num = 0.9):
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

    def click_point_until(self,point,key,num = 0.9):
        log(f'click_point_until:开始获取 {key}')
        while not self.check_one_pic(key, num, self.processed_screen):
            control.click(point)
        log(f'click_point_until:已捕获 {key}')

    def run_until(self,name,key,num = 0.9):
        log(f'run_until:开始朝{name}移动')
        while not self.check_one_pic(name, num, self.processed_screen):
            control.send_key(key, 0.5)
        log(f'run_until:已移动到{name}位置')

    def run(self,t):
        control.send_key_down('w')
        time.sleep(0.3)
        control.send_key_down('shift')
        time.sleep(t)
        control.send_key_up('shift')
        time.sleep(0.3)
        control.send_key_up('w')

    def scroll_click(self,name1,name2,num = 0.9):
        while self.match_one_pic(name1,num) is None:
            if not self.match_one_pic(name2, num):
                log(f'{name2}', self.match_one_pic(name1, num))
                continue
            log(f'{name2}未找到 继续滑动')
            point = self.match_one_pic(name2,num)[0]
            control.scroll(-1, point)
            time.sleep(1)
        while 1:
            item_point = self.match_one_pic(name1,num)
            if item_point is None:
                break

            for i in self.match_pics(name2,num):
                if item_point[0][1]<i['y']+100:
                    control.click([i['x'],i['y']])
                    break
        log(f'scroll_click:已查找到{name1}')
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

    def check_pic(self,names,num):
        processed_screen = get_pic(self.wt)
        res = {}
        for name in names:
            match = self.check_one_pic(name,num,processed_screen)
            if match:
                res[name] = match
        return res

    def show_pic(self):
        window_name = "Processed Screen"
        while True:
            t0 = time.time()
            processed_screen = get_pic('原神')
            if processed_screen is None:
                continue
            # processed_screen = reset_pic(processed_screen, 1600, 900)
            cv2.imshow(window_name, processed_screen)
            # set_window_topmost(window_name)  # 设置窗口置顶
            # 退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            log(f'总用时 {time.time() - t0}')

        cv2.destroyAllWindows()

def show_real_time_match():
    window_name = "Processed Screen"
    while True:
        # 获取并处理当前屏幕区域
        processed_screen = get_pic("原神")
        cv2.imshow(window_name, processed_screen)
        p1, p2 = [[380, 45], [416, 81]]
        x, y, w, h = p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1]
        processed_screen = processed_screen[y:y + h, x:x + w]  # 裁剪图像
        # 退出条件
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # 控制每秒处理一次
        time.sleep(0.2)

    cv2.destroyAllWindows()


if __name__ == '__main__':
    c = check('原神','games/ys/image/','games/ys/data/img_loc.json')
    c.check_start()
    c.show_pic()

