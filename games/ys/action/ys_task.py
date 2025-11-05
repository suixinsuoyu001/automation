from func.common import *
from func.check import *
import pyautogui

pyautogui.FAILSAFE = False  # 禁用 fail-safe

image_path = 'games/ys/image/'
json_path = 'games/ys/data/img_loc.json'

c = check('原神',image_path,json_path)

def pic_click(names,matches):
    for i in names:
        if i in matches:
            pyautogui.click(get_position(matches[i][0]))
            return

def pic_press(names,matches,s):
    for i in names:
        if i in matches:
            pyautogui.press(s)
            return



def talk():
    while True:
        click_names = ['对话标识1',
                       ]
        esc_names = []
        space_names = ['剧情标识','对话标识2']
        names = []
        matches = c.check_pic(click_names+esc_names+space_names+names,0.85)
        focus = get_focus_window()
        if focus and '原神' in focus:
            print(matches)
            pic_click(click_names, matches)
            pic_press(esc_names, matches,'esc')
            pic_press(space_names, matches, 'space')



        time.sleep(0.1)

if __name__ == '__main__':
    res = c.t_match.save_pic_loc('剧情标识',json_path)
    # print(res)
    # talk()
