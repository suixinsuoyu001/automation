from datetime import datetime
import sys, pyautogui, time, multiprocessing, sys
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from func.common import *


date = datetime.now()
weekday_number = date.weekday() + 1

def write(content):
    with open(r'C:\Users\guoch\Desktop\每日日志.txt', 'a', encoding='utf-8') as file:
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f'{t} {content}\n')  # 写入文本内容


def run_process_with_timeout(fun, timeout):
    t = time.time()
    # 创建一个进程
    process = multiprocessing.Process(target=fun)
    # 启动进程
    process.start()
    # 设置超时时间 (2小时)
    # 等待进程完成，最多等待timeout秒
    process.join(timeout)
    # 如果进程还没结束，则超时并终止进程

    fun_name = fun.__name__

    if process.is_alive():

        print("超时，终止进程")
        write(f"{fun_name}超时，终止进程")
        process.terminate()
        process.join()  # 确保进程完全结束
    else:
        print("任务完成")
        write(f"{fun_name}任务完成 用时 {round(time.time() - t, 2)}")


def BT_login():
    print('崩铁每日登录')
    wake_screen()
    from games.starRail.execute.bt_mr import mr_execute
    mr_execute()
    close_exe('starrail')



def YS_login():
    print('原神登录')
    wake_screen()
    from games.ys.execute.ys_mr import run
    run()
    close_exe('yuanshen')


if __name__ == "__main__":

    hour = date.time().hour
    print(hour)
    if hour == 13:
        run_process_with_timeout(BT_login, 60*60*1.5)

    if hour == 17:
        run_process_with_timeout(YS_login, 60*60*2)


