# -*- coding: utf-8 -*-
"""check_start / Control 的回归测试：游戏没打开就执行任务不会报错。

覆盖：
  1. 鸣潮：check_start 点的是「鸣潮图标」（模板存在），不再 FileNotFoundError
  2. 原神：check_start 点的是「图标2560」，且 control.hwnd 绑的是原神窗口
  3. 图标模板不存在时只记日志、不抛异常，任务继续等窗口
  4. global_match.click(timeout=..) 找不到图标会超时返回 False，不再死等
  5. Control 不再写死鸣潮窗口，而是绑本游戏（老的无参调用行为保持不变）
  6. **入口 focus_or_start_game() + check_start() 只点一次图标**
     （原神批量登录报的「Multiple games are detected. Please exit the
      existing client. Error Code:(3,0,0)」就是入口点一次、check_start 又点
      一次，把单实例启动器拉起两个造成的）
  7. 游戏本体进程已经在跑 -> 不点图标（它只是窗口还没画出来）
  8. 短观察期（默认 0.3 秒）内窗口自己出现 -> 不点图标，且**一出现就返回**
  9. 窗口已经在 -> 只还原 + 置前，不点图标
  10. 崩铁（自己的 check 类）也走同一套防护
  11. 米哈游启动器进程在跑、窗口还没出来 -> 追加等待（有上限）
  12. 启动器缩在托盘里（窗口一直不出来）-> 有上限地等完照常点图标，不卡死

全程不真的点桌面（pyautogui / 窗口句柄都做了替身），只跑逻辑，约 20 秒。
运行：venv\\Scripts\\python.exe tool/check_start_test.py
需要把输出（含 log 里的 ANSI 颜色码）存成文件时：
  set CHECK_START_TEST_LOG=tool/check_start_test.log
"""
import os
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, r'e:\python\automation')

# 有些终端（IDE/CI）抓不全多行输出，可用环境变量把输出重定向到文件
_log_path = os.environ.get('CHECK_START_TEST_LOG')
if _log_path:


    class _Tee:
        def __init__(self, path):
            self._f = open(path, 'w', encoding='utf-8')

        def write(self, s):
            self._f.write(s)
            self._f.flush()

        def flush(self):
            self._f.flush()


    sys.stdout = sys.stderr = _Tee(_log_path)

import func.check as checkmod  # noqa: E402
import func.common as common  # noqa: E402
import func.control.global_match as gm  # noqa: E402

FAKE_HWND = 4242
# 窗口出现的时刻：比 0.3 秒的观察期晚一点（0.5 秒），
# 这样「该点图标的用例」真的会点图标，而 check_start 的等窗口循环也不会真的死等。
WINDOW_APPEARS_AFTER = 0.5
state = {'t0': 0.0}


def fake_get_hwnd(title):
    if not state['t0']:
        return None
    return FAKE_HWND if time.time() >= state['t0'] + WINDOW_APPEARS_AFTER else None

class SpyMatch:
    """假的 g_match：记录被点的是哪张图，不真的操作桌面。"""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def click(self, name, num=None, timeout=None):
        self.calls.append((name, timeout))
        if self.fail:
            raise FileNotFoundError(f'文件不存在: {name}.png')
        return True




def use_fake_hwnd():
    """把「找窗口」换成替身。

    check_start / focus_or_start_game 用的是 func.check 里
    `from func.common import *` 进来的那份引用，
    start_game_if_missing 用的是 func.common 自己命名空间里的那份，
    所以两个模块都要打（这也是这套代码里 import * 的固有坑）。
    """
    checkmod.get_hwnd = fake_get_hwnd
    common.get_hwnd = fake_get_hwnd


def no_game_process(exe_names=None):
    """测试环境里保证「没有游戏进程在跑」，让点图标的逻辑真的走到。"""
    return False


def reset(c):
    c.g_match = SpyMatch()
    state['t0'] = time.time()
    use_fake_hwnd()
    # 每个用例开始前清掉「刚点过图标」的冷却记录，否则后面的用例会被它挡住
    common._game_started_at.clear()
    common.game_process_running = no_game_process
    # 真机上「米哈游启动器」可能缩在托盘里，测试里默认当作没在跑（用例 11/12 单独测）
    common.launcher_running = lambda: False
    # 观察期默认 0.3 秒（用例 8/11/12 会单独设）
    common.GAME_START_GRACE = 0.3
    common.GAME_START_LAUNCHER_GRACE = 2.5
    return c


use_fake_hwnd()
common.game_process_running = no_game_process
common.launcher_running = lambda: False
common.GAME_START_GRACE = 0.3
common.GAME_START_LAUNCHER_GRACE = 2.5


ok = []
fail = []


def check(title, cond, extra=''):
    (ok if cond else fail).append(f'{title} {extra}')
    print(('  [OK]   ' if cond else '  [FAIL] ') + title + (f'  {extra}' if extra else ''))


print('=' * 72)
print('1) 鸣潮：check_start 用「鸣潮图标」，不再 FileNotFoundError')
import games.mc.action.mc_task as mc_task  # noqa: E402

c = reset(mc_task.c)
print('   mc.icon =', repr(c.icon), ' mc.wt =', repr(c.wt))
check('mc.icon 是鸣潮图标', c.icon == '鸣潮图标', c.icon)
c.check_start()
check('mc 没抛异常且点了鸣潮图标', c.g_match.calls == [('鸣潮图标', 60)], c.g_match.calls)
check('mc control.hwnd 绑到鸣潮窗口', c.control.hwnd == FAKE_HWND, c.control.hwnd)
checkmod.stop_capture()

print('=' * 72)
print('2) 原神：check_start 用「图标2560」，control.hwnd 绑原神窗口（不是鸣潮）')
import games.ys.action.ys_action as ys_action  # noqa: E402

c = reset(ys_action.c)
print('   ys.icon =', repr(c.icon), ' ys.wt =', repr(c.wt))
check('ys.icon 是 图标2560', c.icon == '图标2560', c.icon)
c.check_start()
check('ys 点了 图标2560', c.g_match.calls == [('图标2560', 60)], c.g_match.calls)
check('ys control.hwnd 绑到原神窗口', c.control.hwnd == FAKE_HWND, c.control.hwnd)
checkmod.stop_capture()

print('=' * 72)
print('3) 图标模板不存在：只记日志，不抛异常（老代码这里是 FileNotFoundError）')
c = reset(mc_task.c)
c.g_match = SpyMatch(fail=True)
try:
    c.check_start()
    crashed = False
    err = ''
except Exception as e:            # noqa: BLE001
    crashed = True
    err = repr(e)
check('模板缺失不再打挂任务', not crashed, err)
checkmod.stop_capture()

print('=' * 72)
print('4) global_match.click(timeout=..)：找不到图标超时返回 False')


class NoMatch(gm.match):
    """模板文件存在，但屏幕上永远找不到。"""

    def find_image_on_screen(self, name, threshold=0.8):
        return []


m = NoMatch('games/ys/image/', 0.85)
t0 = time.time()
res = m.click('图标2560', timeout=2)
dt = time.time() - t0
check('超时返回 False', res is False, f'返回={res} 用时={dt:.2f}s')
check('约 2 秒就放弃（不再死等）', 1.8 <= dt <= 5, f'{dt:.2f}s')


class AlwaysMatch(gm.match):
    """屏幕上一定有。"""

    def find_image_on_screen(self, name, threshold=0.8):
        return [(11, 22)]


real_pyautogui = gm.pyautogui
clicked = []
gm.pyautogui = SimpleNamespace(click=lambda p: clicked.append(p))
try:
    res = AlwaysMatch('games/ys/image/', 0.85).click('图标2560', timeout=2)
finally:
    gm.pyautogui = real_pyautogui
check('找到时仍然返回 True 并点击', res is True and clicked == [(11, 22)], f'返回={res} 点击={clicked}')

print('=' * 72)
print('5) Control 不再写死鸣潮窗口')
import func.control.mc_control as mc_control  # noqa: E402

Control = checkmod.Control
# Control() 内部的 get_hwnd 来自 mc_control 自己的命名空间，所以要打在这里
mc_control.get_hwnd = lambda title: 777 if title == '鸣潮  ' else None
check('Control() 保持老行为：仍取鸣潮窗口', Control().hwnd == 777, Control().hwnd)
check('Control(None) 保持 None，不会串到鸣潮窗口', Control(None).hwnd is None, Control(None).hwnd)
check('Control(hwnd) 用传入的句柄', Control(888).hwnd == 888, Control(888).hwnd)
checkmod.get_hwnd = lambda title: 'HWND-' + title
fresh = checkmod.check('原神', 'games/ys/image/', 'games/ys/data/img_loc.json')
check('check 实例的 control 绑自己的游戏窗口', fresh.control.hwnd == 'HWND-原神', fresh.control.hwnd)
print('   Control 来自模块:', mc_control.Control.__module__)

print('=' * 72)
print('6) 入口 + check_start 只点一次图标（批量登录弹的那个报错就是这么来的）')
c = reset(ys_action.c)
c.focus_or_start_game()          # 入口：窗口不在 -> 点一次图标把游戏拉起来
c.check_start()                  # 紧接着 check_start：绝不能又点一次
check('整个入口只点了一次图标', c.g_match.calls == [('图标2560', 60)], c.g_match.calls)
checkmod.stop_capture()

print('=' * 72)
print('7) 游戏本体进程已经在跑 -> 不点图标（它只是窗口还没画出来）')
c = reset(ys_action.c)
print('   ys.exe =', c.exe)
check('原神注册了本体进程名', 'yuanshen.exe' in c.exe, c.exe)
common.game_process_running = lambda exe_names: 'yuanshen.exe' in list(exe_names or ())
c.check_start()
check('进程在就不点桌面图标', c.g_match.calls == [], c.g_match.calls)
checkmod.stop_capture()

print('=' * 72)
print('8) 短观察期：窗口在这期间自己出现 -> 不点图标，而且几乎不花时间')
c = reset(ys_action.c)
_t8 = {'t': 0.0}


def window_after_150ms(title):
    if _t8['t'] == 0.0:
        _t8['t'] = time.time()
    return FAKE_HWND if time.time() - _t8['t'] >= 0.15 else None


checkmod.get_hwnd = window_after_150ms
common.get_hwnd = window_after_150ms
t0 = time.time()
try:
    c.start_game()
finally:
    dt = time.time() - t0
    use_fake_hwnd()
check('窗口出现就没点图标', c.g_match.calls == [], c.g_match.calls)
check('窗口一出现马上返回（不等固定时长）', 0.15 <= dt <= 0.5, f'{dt:.3f}s')

print('=' * 72)
print('9) 窗口已经在 -> 只还原 + 置前，不点图标')
c = reset(ys_action.c)
checkmod.get_hwnd = lambda title: FAKE_HWND           # 窗口已经在
moved = []
_real_game_start = checkmod.game_start
checkmod.game_start = lambda wt: moved.append(wt)
try:
    c.focus_or_start_game()
finally:
    checkmod.game_start = _real_game_start
check('窗口在时只置前', moved == ['原神'] and c.g_match.calls == [],
      f'置前={moved} 点图={c.g_match.calls}')

print('=' * 72)
print('10) 崩铁（自己的 check 类）也走同一套防护')
import games.starRail.action.bt_func as bt_func  # noqa: E402

bt_func.get_hwnd = fake_get_hwnd
b = bt_func.check('崩坏：星穹铁道')
b.g_match = SpyMatch()
state['t0'] = time.time()
common._game_started_at.clear()
common.launcher_running = lambda: False
print('   bt.icon =', repr(b.icon), ' bt.exe =', b.exe)
check('崩铁图标模板是 图标2560', b.icon == '图标2560', b.icon)
check('崩铁注册了本体进程名', 'starrail.exe' in b.exe, b.exe)
b.focus_or_start_game()
check('崩铁窗口不在时点一次图标', b.g_match.calls == [('图标2560', 60)], b.g_match.calls)

print('=' * 72)
print('11) 米哈游启动器在跑、窗口还没出来 -> 追加等一小会儿（有上限）')
c = reset(ys_action.c)
common.GAME_START_GRACE = 0.1
common.GAME_START_LAUNCHER_GRACE = 0.5          # 测试里调小，真机默认 2.5 秒
common.launcher_running = lambda: True
_t11 = {'t': 0.0}


def window_after_300ms(title):
    if _t11['t'] == 0.0:
        _t11['t'] = time.time()
    return FAKE_HWND if time.time() - _t11['t'] >= 0.3 else None


checkmod.get_hwnd = window_after_300ms
common.get_hwnd = window_after_300ms
t0 = time.time()
try:
    c.start_game()
finally:
    dt = time.time() - t0
    use_fake_hwnd()
check('启动器在跑时不急着点图标', c.g_match.calls == [], c.g_match.calls)
check('追加等待有上限（真机 2.5 秒，绝不是原来那种久等）', 0.25 <= dt <= 1.2, f'{dt:.3f}s')

print('=' * 72)
print('12) 启动器只是缩在托盘里（窗口一直不出来）-> 有上限地等完照常点图标')
c = reset(ys_action.c)
common.GAME_START_GRACE = 0.1
common.GAME_START_LAUNCHER_GRACE = 0.4
common.launcher_running = lambda: True
checkmod.get_hwnd = lambda title: None
common.get_hwnd = lambda title: None
t0 = time.time()
try:
    c.start_game()
finally:
    dt = time.time() - t0
    use_fake_hwnd()
check('托盘的启动器不会把任务卡死', c.g_match.calls == [('图标2560', 60)], c.g_match.calls)
check('最多多等 GAME_START_LAUNCHER_GRACE 秒', 0.35 <= dt <= 1.2, f'{dt:.3f}s')

print('=' * 72)
print(f'通过 {len(ok)} 项，失败 {len(fail)} 项')
if fail:
    for f in fail:
        print('  FAIL:', f)
    sys.exit(1)
print('全部通过')
