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
screenshot.stop_capture()             # 停止
```

* `func.get_pic.get_pic(window_title)` 签名不变，服务已启动时直接返回共享帧，
  未启动时自动回退为单次实时截图 —— 老代码**零改动**即可受益。
* 三个 `check` 类的 `processed_screen` 都改成了读取共享服务的 `property`，
  崩铁的 `get_pic_loop` 只保留「跟踪焦点窗口 + 窗口重启后重建句柄」的
  维护工作，不再重复截图。
* 循环线程每帧都产生**全新 ndarray** 再整体替换引用，从不原地修改，
  因此 `latest()` 可以零拷贝返回，调用方不会读到撕裂画面。

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
