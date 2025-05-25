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

if __name__ == '__main__':
    c = check(windows_title)
    c.check_start()
    # # c.save_pic_loc('点击进入')
    c.show_pic()

