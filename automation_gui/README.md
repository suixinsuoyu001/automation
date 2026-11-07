# 自动化助手 (Automation GUI)

一个基于 **PySide6 + PySide6-Fluent-Widgets** 的图形化自动化工具，页面风格参考 [ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)（Fluent Design 流畅设计）。

它把 `games/ys/execute`、`games/starRail/execute`、`games/mc/execute` 下的自动化脚本封装成可视化任务，支持一键运行、参数配置、账号管理与实时日志。

## 功能

- **任务页**：顶部按游戏切换（原神 / 崩铁 / 鸣潮，**默认原神**），**一行两个**卡片，
  卡片上是任务名、说明与参数，底部「开始任务 / 停止任务」。
  「原神圣遗物秘境」排在最前面，且只需选秘境、不用选账号。
  「自动剧情」这类需要一直跑、手动停的持续任务，在最上方用**开关**表示
  （打开=开始任务，关闭=停止任务），不再用「选中 + 开始」。
- **账号页**：可视化增删改原神 / 崩铁账号列表，保存到 `accounts.json`。
- **秘境配置页**：可视化编辑「圣遗物秘境编号 → 模板图片名」映射，写入
  `games/ys/data/秘境圣遗物.json`（游戏脚本读的是同一份文件，改完立即生效）。
  选中条目时右侧会**预览对应的模板图片**，并显示原始尺寸与文件路径，方便确认
  「名字有没有指错图」；图片缺失时给出提示（含期望路径）。
- **全局快捷键**：前缀键默认 `+`（键盘上的 `Shift`+`=`）。
  * `+1` ~ `+9` —— 登录原神第 1~9 个账号（即序号 0~8）。小键盘的 `+` 也可以。
  * `+t` —— 开/关**原神自动剧情**（和界面上的开关同步）。
  * 前缀键 / 剧情键可改：见 `main_window.py` 里的
    `MainWindow.快捷键前缀`、`MainWindow.剧情快捷键`；
  * 按完 `+` 后**没松开 Shift 直接按数字**也能识别（此时数字会变成 `!@#…`）；
  * 走 **pynput 全局键盘钩子**，所以**焦点在游戏窗口时也生效**（Qt 的 `QShortcut`
    只在程序窗口激活时才触发，不满足这个场景）；
  * **账号不足时不会执行**，只给一条提示（例如只有 3 个账号时按 `+4` 无动作）；
  * 在本窗口的输入框里打字时不会抢按键；
  * **任务运行期间会忽略登录快捷键** —— 自动化会用 `keyboard.write` 输入账号/兑换码，
    全局钩子能收到这些模拟按键，不挡掉就可能误触发登录。
    （`+t` 例外：只有当正在跑的**就是剧情任务**时才响应，用来把它关掉。）
- **日志页**：实时显示任务运行日志，按级别着色。
- **主题切换**：左下角按钮在浅色 / 深色主题间切换。

## 安装依赖

```bash
pip install -r automation_gui/requirements.txt
```

> 说明：`onnxruntime` 固定为 `1.18.1`，因为 1.23 在部分 Windows 上会出现
> `DLL load failed while importing onnxruntime_pybind11_state` 错误。
> 若下载缓慢可加国内镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`

## 运行

在项目根目录 `e:\python\automation` 下执行：

```bash
python -m automation_gui.main
```

或：

```bash
python automation_gui/main.py
```

## 目录结构

```
automation_gui/
├── main.py                 # 程序入口
├── config.py               # 全局配置（窗口、账号默认值、任务元数据）
├── requirements.txt        # 依赖
├── accounts.json           # 账号列表（首次运行自动生成）
├── core/
│   ├── task_runner.py      # 子进程任务执行器（支持强制停止）
│   ├── tasks.py            # 任务注册表（映射到 games/* 下的函数）
│   ├── account_store.py    # 账号读写
│   ├── domain_store.py     # 秘境映射读写（games/ys/data/秘境圣遗物.json）
│   └── logger.py           # 日志记录
└── ui/
    ├── main_window.py      # 主窗口（FluentWindow + 左侧导航）
    ├── home_page.py        # 任务页
    ├── account_page.py     # 账号页
    ├── config_page.py      # 秘境配置页
    └── log_page.py         # 日志页
```

## 扩展任务

在 `core/tasks.py` 中新增 `TaskDef` 即可，`entry` 使用 `模块路径:函数名` 形式，例如：

```python
TaskDef(
    id="ys_xxx",
    name="我的任务",
    description="说明",
    entry="games.ys.execute.xxx:run",
    group="原神",
    params=[TaskParam("n", "序号", "int", 0, minimum=0, maximum=9)],
)
```

### 参数类型

| `type` | 渲染控件 | 说明 |
|---|---|---|
| `int` | 数字输入框 | 配合 `minimum` / `maximum` |
| `choice` | 下拉框 | 配合 `choices=[(值, 显示文本), ...]`，**界面上显示名称，传回任务函数的仍是原始值** |

`choices` 也可以传一个**函数**（惰性求值），这样选项能实时反映账号页的改动，例如
「原神圣遗物秘境」就是用它来显示账号名与秘境名：

```python
TaskParam("zh_num", "账号", "choice", 0, choices=ys_account_choices)
TaskParam("num",    "秘境", "choice", 1, choices=ys_domain_choices)
```

改完账号页后，任务卡片上的下拉选项会自动同步刷新（`AccountPage.accountsChanged`
→ `HomePage.refresh_params`），无需重启程序。

## 架构说明

### 通用循环截图服务（`func/screenshot.py`）

原神 / 崩铁 / 鸣潮 三个 `check` 类原先各自维护一个截图线程，而且每轮还会
重复调用两次 `get_pic`（单次 `PrintWindow` 约 10~30ms），CPU 浪费严重。

现在统一为**进程内单例**的循环截图服务，所有功能共享同一份最新画面：

```python
from func import screenshot

screenshot.start_capture('原神')     # 启动（重复调用同一窗口不会重启线程）
frame = screenshot.latest('原神')     # 零拷贝取最新一帧
screenshot.is_stale()                 # 画面是否已陈旧（连续失败，别拿它做判断）
screenshot.restart_capture()          # 杀掉截图线程并重新拉起（卡死的旧线程直接放弃）
screenshot.stop_capture()             # 停止
```

* `capture_restart_count()` / `last_frame_age()` 给排查用：前者是本次会话彻底重启了
  几次截图线程，后者是「最近一帧距今多少秒」（180 秒没有任何新帧就会被判成进程级故障）。

* `func.get_pic.get_pic(window_title)` 签名不变，服务已启动时直接返回共享帧，
  未启动时自动回退为单次实时截图 —— 老代码**零改动**即可受益。
* 三个 `check` 类的 `processed_screen` 都改成了读取共享服务的 `property`，
  崩铁的 `get_pic_loop` 只保留「跟踪焦点窗口 + 窗口重启后重建句柄」的
  维护工作，不再重复截图。
* 循环线程每帧都产生**全新 ndarray** 再整体替换引用，从不原地修改，
  因此 `latest()` 可以零拷贝返回，调用方不会读到撕裂画面。

### 截图失败时的自我保护（`func/screenshot.py`）

**真机结论：崩铁「全屏」时 PrintWindow 一定抓不到画面，而且只有屏幕 DC 能救命。**
全屏游戏窗口是 popup 且盖满屏幕，一旦它成为**前台窗口**，DWM 就切到 direct-flip
（不再合成这个窗口）：`PrintWindow` 的 `0/1/2/3` 四种 flag **全部返回 0**、只得到
全黑位图，`DwmFlush` 也没用；更关键的是**从窗口 DC（`GetWindowDC`）BitBlt 同样是
纯黑** —— flip 的内容压根不在窗口 DC 里。唯一能拿到真画面的是**屏幕 DC**
（`GetDC(0)` 拷客户区所在的那块屏幕，实测均值 65、唯一色 36 万，模板匹配
0.66~0.75）。现象就是「跑着跑着突然一直报 `PrintWindow函数截取窗口图像失败`、
任务失效」，而重新开关任务（人动一下鼠标、GUI 抢回前台）又好了。所以现在的处理是：

* **抓屏幕回退**：PrintWindow 全失败、且**屏幕上采样点确实都是本窗口**（
  `_window_visible_ratio`，5×5 采样 ≥80%）时，从**屏幕 DC** 拷客户区那一块
  （进程已 `SetProcessDPIAware`，坐标与 2560×1440 的模板坐标一致）。闸门**不能**
  用 `GetForegroundWindow`：切窗口时前台会短暂变成系统内部窗口（`ForegroundStaging`、
  任务切换的 `MultitaskingViewFrame`，实测 4 秒跳 249 次），会把明明能抓的画面
  误判掉。窗口真的被盖住/切走时坚决不用（否则会把上层窗口的像素当游戏画面乱点，
  见 `BITBLT_FALLBACK`），并且日志会说清楚**是谁挡住了**（类名 + 标题）。
* **全屏游戏被切走会自动抢回前台**：全屏窗口被切到别的窗口后面时，PrintWindow
  必失败、抓屏幕又必须拒绝 —— 等于完全抓不到，唯一出路是把它弄回屏幕。此时截图
  服务会（`RECOVER_INTERVAL` 15s 起、连续失败指数退避到 5 分钟）把游戏窗口
  `SW_RESTORE` + 抢回前台，画面自己就回来了，不用重开任务。
  抢前台的实现有坑：**后台进程调用 `SetForegroundWindow` 会被系统静默忽略**
  （不报错、什么也不发生），所以先发一次 ALT 空按让系统认为「最后输入来自本进程」，
  再 `SetForegroundWindow`，还不行就挂到前台窗口线程 / 目标线程上重试，最后用
  `GetForegroundWindow` 判断到底成没成。置前动作跑在独立线程里，万一
  `AttachThreadInput` 卡住也不会把截图线程拖死。
* **用户正在用电脑时不自愈，等他空闲**：抢焦点会打断正在打字的人，所以自愈要求
  「**真人** `RECOVER_MIN_USER_IDLE`（60s）内没碰过键鼠」（`real_user_idle`，
  会扣掉我们自己注入的空输入，否则永远以为自己刚有操作）。日志会说明「先不动它，
  等你停下 60s 后自动弄回来」。想彻底不抢焦点：把崩铁改成**窗口化**模式 —— 窗口
  模式下 DWM 正常合成，PrintWindow 在游戏不在前台时也能抓到画面。
* **日志限频**：原实现每帧都 `log(...)`，失败时就是 20~100Hz 刷屏。现在用
  `log_throttled(key, msg, 5s)`，并把失败原因 + **窗口状态**（最小化 / 不可见 /
  cloaked / 没响应 / 会话被锁 / 距上次真实输入多少秒）写在同一条日志里。
* **纯色图判失败**：窗口最小化 / 画面被系统丢掉时 PrintWindow 会「成功」返回
  全黑图，模板匹配永远匹配不到 —— 现在直接当失败处理（`_is_blank`）。
* **自动还原**：窗口最小化/不可见且真人空闲 60s 以上时自动
  `ShowWindow(SW_RESTORE)` + 置前，任务不用重开就能继续。
* **失败降频**：连续失败时重试间隔拉到 `FAIL_RETRY_INTERVAL`（1 秒），重新按标题
  找窗口限频到 `RESOLVE_INTERVAL`（3 秒）；抓到一帧立刻恢复原频率。
* **画面陈旧标记**：连续失败 `STALE_AFTER_FAILURES`（3）次后 `screenshot.is_stale()`
  为真，`func.check` / `bt_func` 的 `check_one_pic` 会**跳过识别**（只等截图恢复），
  不再拿过期的那一帧乱点（这是「功能失效 / 乱点 / 切窗口变卡」的直接原因）。
* **别让系统关屏/休眠/锁屏**：自动化点击走 `PostMessage`，系统**不算用户输入**，
  长时间跑剧情时显示器会照样关、会话会照样锁，而锁屏后 DWM 停止合成用户桌面 →
  PrintWindow 全挂。所以截图线程会 `SetThreadExecutionState(ES_DISPLAY_REQUIRED)`
  并且每 `WAKE_INTERVAL`（20s）注入一次空输入（`keep_awake`）。注意：**实测
  「注入空输入」并不总能顶掉 Windows 的空闲计时器**，所以真正起作用的是
  SetThreadExecutionState；如果诊断显示屏保才是罪魁，把 `SUPPRESS_SCREENSAVER`
  改成 True（截图期间临时禁用屏保，停止时还原）。
* **GDI 清理**：删位图前先 `SelectObject` 换出来，避免长时间运行泄漏位图。
* **`get_hwnd` 跳过本进程的窗口**：`GetWindowText` 对**本进程**的窗口是同步等
  `WM_GETTEXT` 的，本进程里只要有个窗口没在抽消息，截图线程就会**永久卡死**
  且没有任何报错（表现就是「功能失效」）。游戏窗口永远在别的进程，所以直接跳过。
* **杀掉截图线程并重新拉起（看门狗）**：线程一旦卡在 `PrintWindow` / `GetDC` 这类
  **系统调用**里，Python 侧没有任何办法打断它（GIL 早就释放了，只能等调用返回），
  表现就是画面永远不再更新、怎么等都不会自己好。所以另起一个 `ScreenshotWatchdog`
  线程盯着，命中任一条就 `restart_capture()`：

  * 连续失败 `HARD_RESTART_AFTER_FAILURES`（10 次 ≈ 10 秒 —— 失败期间每秒才重试一帧）；
  * 超过 `LOOP_HANG_TIMEOUT`（20s）没有心跳 —— 也就是卡在系统调用里；
  * 截图线程直接退出（异常 / 被系统回收）。

  重启 = 放弃旧线程（daemon，进程退出时一并回收）、`GdiFlush`、清掉限频 / 陈旧 /
  退避计数、重新按标题找窗口、起新线程（线程名 `ScreenshotLoop#N`，N 是代次），
  日志会明确写一句「已杀掉截图线程（第 N 次），正在重新拉起：<原因>」。
  两次重启之间有指数退避（`HARD_RESTART_INTERVAL` 15s 起，最长 5 分钟），避免故障
  一直存在时反复换线程反而更卡。旧线程醒来退出时按代次判断「我已经被换掉了」，
  不会去撤新线程的保活 / 屏保状态。
* **换线程也救不回来时只报警，不擅自杀任务进程**：任务子进程里还有一个看护线程，
  只要「画面连续 `CAPTURE_DEAD_SECONDS`（180s）一帧都没有、且截图服务自己判陈旧」，
  就往日志队列里上报 `capture_dead`；界面默认只写一条错误日志 + 弹提示（把游戏
  窗口切回前台 / 改成窗口化模式后会自动恢复），**不杀任务、不抢焦点** —— 因为抢
  焦点会打断正在用电脑的人。想让程序自动把整棵任务进程树收掉再按原参数重开（含
  任务脚本自己起的点击子进程，最多 2 次），把
  `automation_gui/ui/main_window.py` 里的 `AUTO_RESTART_ON_CAPTURE_DEAD` 改成 `True`。

出问题时先跑现场诊断（只读，会把窗口状态 / 空闲时间 / 屏保 / 电源设置都打出来）：

```bash
venv\Scripts\python.exe tool/capture_diagnose.py            # 默认崩坏：星穹铁道
venv\Scripts\python.exe tool/capture_diagnose.py 原神
```

回归测试（在独立进程里建一个窗口当截图目标，61 项断言，约 50 秒）：

```bash
venv\Scripts\python.exe tool/screenshot_capture_test.py
```

### `check_start` 与「游戏还没打开」的处理（`func/check.py`）

原神 / 崩铁 / 鸣潮 都用 `func/check.py` 的 `check` 类，`check_start()` 里原来有两处
写死了鸣潮，导致「刚双击完游戏图标、游戏还没打开就点开始任务」直接报错或按键发错窗口：

* **桌面图标模板按游戏区分**：`check(wt, path, json_path, icon=None)` 新增 `icon` 参数，
  默认 `图标{屏幕宽}`（`setting.json` 的 `resolution[0]` 决定文件名，原神 / 崩铁都是
  这个约定），鸣潮的图标叫「鸣潮图标」，所以在 `games/mc/action/mc_task.py` 里显式传入。
* **点图标不再抛异常**：`start_game()` 用 `global_match.click(icon, timeout=60)` 限时找图标，
  模板文件不存在（以前这里是 `FileNotFoundError`，直接把任务打挂）或超时找不到，
  都只记一条日志、返回 `False`，然后照常执行「等待窗口出现」的老流程。
* **`control` 绑的是本游戏的窗口**：`check_start()` 里原本是写死的 `get_hwnd('鸣潮  ')`，
  跑原神 / 崩铁时按键和点击会发到鸣潮窗口（鸣潮没开就是 `None`，等于什么都不点）。
  现在统一用 `get_hwnd(self.wt)`；`Control(hwnd)` 也支持由调用方传入句柄，
  `Control()` 不传时保持老行为。

### 只允许点一次桌面图标：`Multiple games are detected` (3,0,0)（`func/common.py`）

原神批量登录会弹

```
Multiple games are detected.
Please exit the existing client.
Error Code:(3,0,0)
```

原因是**同一秒内点了两次桌面图标**：任务入口（`ys_login.logins` 等）自己写了
`c.g_match.click(f'图标{resolution[0]}')`，紧接着 `check_start()` 里的 `start_game()`
发现窗口还没出现，又点了一次 —— 原神和崩铁共用的是一个**单实例**启动器，
被拉起两次就弹这个对话框，之后游戏再也起不来，任务只能卡死在「等待窗口」。

现在所有「把游戏启动起来」的动作都统一走 `func.common.start_game_if_missing()`，
由它保证只点一次：

* **窗口已经在** → 任务入口改调 `check.focus_or_start_game()`：只做「还原 + 置前」
  （登录流程要键盘输入，窗口必须在最前），**绝不点图标**。
* **刚点过一次图标** → `GAME_START_COOLDOWN`（150 秒）内不再点。
* **游戏进程已经在跑** → 说明正在启动（窗口还没画出来），不点，继续等窗口。
  进程名由各游戏注册：`check(..., exe=[...])`，原神 `yuanshen.exe` /
  `genshinimpact.exe`，崩铁 `starrail.exe`（`bt_func.check` 里写死），
  鸣潮 `client-win64-shipping.exe`。
* **米哈游启动器进程已经在跑** → 说明启动器正在起来（窗口还没出来）：追加等
  `GAME_START_LAUNCHER_GRACE`（最多 2.5 秒）看窗口会不会自己出现；超时
  （比如启动器只是缩在托盘里）就照常点图标 —— **不无限等、不卡死**。
  进程名 `launcher.exe` 太通用，所以按 exe 路径里的 `miHoYo Launcher` 目录来认。
* **上面都没命中** → 只留 `GAME_START_GRACE`（0.3 秒）盯窗口：每 40ms 查一次
  `get_hwnd`（EnumWindows 很便宜），窗口冒出来就不点，否则点图标。

冷启动时这一整套判断 + 点图标实测只花 **~0.33 秒**（本机：`get_hwnd` 0.6ms、
进程扫描 26ms、启动器检查 1.2ms，加 0.3 秒观察期）。**不是盲等**：原来那 5 秒
只是为了「万一用户刚好双击了图标」而干等，现在换成确定性的即时信号 + 极短观察期。

* 还在等窗口时，`check_start()` 每 45 秒会再试一次 `start_game()`，
  上一次因为「刚点过 / 进程还在 / 图标被挡住」没点成的情况能自愈（不会连点）。

`games/starRail/action/bt_func.py` 的 `check`（崩铁自己的那份实现）也加了同名的
`start_game()` / `focus_or_start_game()`，行为一致。

回归测试（全程不真的点桌面，句柄与 pyautogui 都用替身，约 25 秒）：

```powershell
venv\Scripts\python.exe tool/check_start_test.py
```

### 任务执行器为什么不能用 daemon（`core/task_runner.py`）

`ys_talk` / `bt_talk` / `bt_auto` / `bt_mnyz` / `mc_jq` / `mc_hd` 这些脚本
内部还会用 `multiprocessing.Process` 起「点击循环」进程。而 Python 规定
**守护进程不允许创建子进程**，一旦用 `daemon=True` 就会立刻抛：

```
AssertionError: daemonic processes are not allowed to have children
```

表现为「任务显示已启动，但游戏毫无反应」。所以 `TaskRunner` 使用
`daemon=False`，并在 `stop()` 时用 `psutil` 递归回收**整棵进程树**，
点「停止任务」不会留下继续点击游戏的孤儿进程。

## 注意事项

- 运行任务前请确保游戏已启动、分辨率与 `setting.json` 一致（默认 2560x1440）。
- 任务在独立子进程中运行，点击「停止任务」会强制结束该进程。
- 部分任务（如批量登录）需要人工按 `0` 继续，请留意游戏窗口。
