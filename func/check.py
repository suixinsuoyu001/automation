from func.get_pic import *
from func.match.template_match import t_match
from func.common import *
from func.basic import *
import threading
from func.control.mc_control import *
from games.ys.match.yolo_match import *
from games.ys.action.ys_funtion import *
from func.control.global_match import match

class check():
    def __init__(self,wt,path,json_path):
        self.wt = wt
        self.path = path
        self.t_match = t_match(wt, path)
        self.locs = read_json(json_path)
        self.size_diff = None
        self.control = Control()
        self.num = 0.85
        self._time_limit = 0.02
        # wait_loop 用的标志位：0=还在等，1=目标已出现
        self.wait_flag = 0
        # 后台线程句柄与停止事件（统一在 __init__ 建好，启停都做幂等处理，
        # 避免重复 start 覆盖属性导致旧线程收不到停止信号而泄漏）
        self.thread2 = None
        self.stop_event2 = None
        self.thread_wait = None
        self._cancel_wait = None
        self.thread_func = None
        self.stop_event_func = None
        self.g_match = match(path, self.num)
        # self.check_game_state()

    # def check_game_state(self):
    #     log(f'等待{self.wt}启动',level=3)
    #     while not get_hwnd(self.wt):
    #         time.sleep(1)
    #     self.check_start()

    @property
    def processed_screen(self):
        """最新一帧画面。

        数据来自 :mod:`func.screenshot` 的**全局通用截图服务**，
        原神 / 崩铁 / 鸣潮所有功能共享同一个截图线程。
        """
        return latest(self.wt)

    @property
    def time_limit(self):
        """截图间隔（秒）。

        老代码里有 ``c.time_limit = 0.2`` 这种「战斗中降频省 CPU」的写法
        （见 ``副本战斗``），现在截图由全局服务统一负责，所以这里赋值时
        会同步改服务间隔，保证原有降频行为不失效。
        """
        return self._time_limit

    @time_limit.setter
    def time_limit(self, value):
        self._time_limit = value
        set_capture_interval(value)

    def check_start(self,time_limit = 0.02):
        """启动全局循环截图。

        重复调用（多个 check 实例/多个功能）不会重复起线程，
        只是把共享服务切到本实例的窗口。
        """
        self.time_limit = time_limit
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
            time.sleep(0.5)
        start_capture(self.wt, time_limit)
        wait_first_frame(self.wt)
        self.control.hwnd = get_hwnd('鸣潮  ')

        self.control.activate()
        log("获取图片进程已开始")

    def check_stop(self):
        stop_capture()
        log("获取图片进程已停止")


    def get_model_res_loop(self, stop_event):
        """后台循环：YOLO 找石化古树（size_diff） + 模板匹配算角色朝向（ego_angle）。

        stop_event 用参数传入，而不是每轮读 ``self.stop_event2``：这样即使
        外面又重新 start 了一轮（属性被覆盖），本线程依然能收到属于自己的
        停止信号，不会变成永远停不下来的孤儿线程。
        """
        # x1, y1 = get_position([200, 130])
        # x2, y2 = get_position([250, 190])
        x1, y1 = [200, 130]
        x2, y2 = [250, 190]
        while not stop_event.is_set():
            time.sleep(self.time_limit2)  # 10ms 检测一次鼠标移动
            screen = self.processed_screen      # 取一次即可，属性访问不必重复
            if screen is None:
                continue
            image = f"{self.path}朝向模板.png"
            cropped = screen[y1:y2, x1:x2]
            self.ego_angle = match_ego_angle(image, cropped)

            match_res = model_match_pic(screen)
            position_x = 2560 // 2
            if match_res:
                size = (match_res[0][0]+match_res[0][2])/2
                self.size_diff = size-position_x
            else:
                self.size_diff = None

    def model_loop_start(self,time_limit = 0.1):
        # 幂等：上一轮如果没停干净先收掉，避免覆盖 thread2 造成线程泄漏
        self.model_loop_end()
        self.time_limit2 = time_limit
        stop_event = threading.Event()
        self.stop_event2 = stop_event
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
            time.sleep(0.5)
        self.thread2 = threading.Thread(
            target=self.get_model_res_loop, args=(stop_event,),
            name='ModelLoop', daemon=True,
        )
        self.thread2.start()
        time.sleep(1)
        log("获取石化古树检出循环已开始")

    def model_loop_end(self,timeout = 2):
        """停止石化古树检出循环（可重复调用）。"""
        stop_event = self.stop_event2
        thread = self.thread2
        if stop_event is None and thread is None:
            return
        self.stop_event2 = None
        self.thread2 = None
        if stop_event is not None:
            stop_event.set()        # 触发停止事件
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout)    # 等待线程结束
        log("获取石化古树检出循环已停止")

    def func_loop(self, func, stop_event):
        while not stop_event.is_set():
            func()
            time.sleep(self.time_limit_func)

    def func_loop_start(self,func,time_limit = 0.01):
        # 幂等：上一轮没停干净先收掉，避免覆盖 thread_func 造成线程泄漏
        self.func_loop_end()
        self.time_limit_func = time_limit
        stop_event = threading.Event()
        self.stop_event_func = stop_event
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
            time.sleep(0.5)
        self.thread_func = threading.Thread(
            target=self.func_loop, args=(func, stop_event),
            name='FuncLoop', daemon=True,
        )
        self.thread_func.start()
        time.sleep(1)
        log(f"{func}循环已开始")

    def func_loop_end(self,timeout = 2):
        """停止 func_loop（可重复调用）。"""
        stop_event = self.stop_event_func
        thread = self.thread_func
        if stop_event is None and thread is None:
            return
        self.stop_event_func = None
        self.thread_func = None
        if stop_event is not None:
            stop_event.set()        # 触发停止事件
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout)    # 等待线程结束
        log("循环已停止")

    def wait_loop(self, name, cancel_event):
        """后台等待 name 出现；出现后把 wait_flag 置 1 供主循环读取。

        被外部取消（新一轮战斗开始）时不置位，否则会把新一轮的
        战斗输出循环立刻打断。
        """
        self.wait_flag = 0
        self.waits([name])
        if cancel_event.is_set():
            log(f'wait_loop {name} 已取消')
            return
        self.wait_flag = 1

    def wait_loop_start(self,name):
        # 幂等：先停掉上一轮，避免「上一轮没检测到目标」时线程越堆越多
        self.wait_loop_end()
        cancel_event = threading.Event()
        self._cancel_wait = cancel_event
        flag = 1
        while not get_hwnd(self.wt):
            if flag:
                log(f'等待{self.wt}启动')
                flag = 0
            time.sleep(0.5)
        self.thread_wait = threading.Thread(
            target=self.wait_loop, args=(name, cancel_event),
            name='WaitLoop', daemon=True,
        )
        self.thread_wait.start()
        time.sleep(1)
        log(f"wait_loop_start {name}循环已开始")

    def wait_loop_end(self,timeout = 2):
        """停止 wait_loop（可重复调用）。"""
        cancel_event = self._cancel_wait
        thread = self.thread_wait
        if cancel_event is None and thread is None:
            return
        if cancel_event is not None:
            cancel_event.set()      # 先通知，再等它退出
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout)
        self._cancel_wait = None
        self.thread_wait = None
        log("wait_loop 循环已停止")


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
            self.control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.control.click(position[0])
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
            self.control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.control.click(position[0])
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
            self.control.activate()
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.control.click(position[0])
                flag = 1
                time.sleep(0.5)
            if flag and not position:
                log(f'wait_click_limit:{name} 已捕获并点击',level=2)
                break
            time.sleep(0.02)
            if time.time() - start_time > t:
                log(f'wait_click_limit:{name} 未捕获，超时取消',level=2)
                break


    def wait_press(self,name,key,num = None):
        if num is None:
            num = self.num
        log(f'wait_press:{name} 开始捕获',level=2)
        flag = 0
        while True:
            self.control.activate()
            # log(num)
            position = self.check_one_pic(name, num, self.processed_screen)
            if position is not None:
                self.control.send_key(key)
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
        last_screen = None
        while True:
            # 被 wait_loop_end 取消时立即退出
            cancel_event = self._cancel_wait
            if cancel_event is not None and cancel_event.is_set():
                return
            screen = self.processed_screen
            if screen is None:
                time.sleep(0.05)
                continue
            if screen is last_screen:
                # 截图服务还没产出新帧，重扫同一张画面结果不会变，
                # 让出 CPU（原实现这里会 100% 占满一个核）
                time.sleep(0.005)
                continue
            last_screen = screen
            for name in names:
                position = self.check_one_pic(name,num,screen)
                if position:
                    log(f'wait: {name} 已找到',level=2)
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
                        self.control.click(position[0])
                        log(f'click_loop_until: 点击 {name}')
                        time.sleep(0.5)
                    else:
                        log(f'click_loop_until: {name} 已捕获 结束循环')
                        return name

    def click_point_until(self,point,key,num = 0.9):
        log(f'click_point_until:开始获取 {key}')
        while not self.check_one_pic(key, num, self.processed_screen):
            self.control.click(point)
        log(f'click_point_until:已捕获 {key}')

    def run_until(self,name,key,num = 0.9):
        log(f'run_until:开始朝{name}移动')
        while not self.check_one_pic(name, num, self.processed_screen):
            self.control.send_key(key, 0.5)
        log(f'run_until:已移动到{name}位置')

    def run(self,t):
        self.control.send_key_down('w')
        time.sleep(0.3)
        self.control.send_key_down('shift')
        time.sleep(t)
        self.control.send_key_up('shift')
        time.sleep(0.3)
        self.control.send_key_up('w')

    def scroll_click(self,name1,name2,num = 0.9):
        while self.match_one_pic(name1,num) is None:
            if not self.match_one_pic(name2, num):
                log(f'{name2}', self.match_one_pic(name1, num))
                continue
            log(f'{name2}未找到 继续滑动')
            point = self.match_one_pic(name2,num)[0]
            self.control.scroll(-1, point)
            time.sleep(1)
        while 1:
            item_point = self.match_one_pic(name1,num)
            if item_point is None:
                break

            for i in self.match_pics(name2,num):
                if item_point[0][1]<i['y']+100:
                    self.control.click([i['x'],i['y']])
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

