"""任务注册表。

把 games/ys/execute 下的功能封装成 UI 可调用的任务定义。
每个任务包含：唯一 id、显示名、描述、图标、参数定义、执行入口。
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TaskParam:
    """任务参数定义。"""
    key: str
    label: str
    type: str = "int"          # int / str / bool / choice
    default: Any = 0
    # choice 类型时的选项：[(值, 显示文本), ...]，也可以是返回该列表的函数，
    # 用函数是为了让「账号」这类选项能实时反映账号页的修改。
    choices: Optional[Any] = None
    minimum: int = 0
    maximum: int = 99

    def option_list(self) -> List:
        """解析选项列表（支持惰性求值的函数）。"""
        choices = self.choices
        if callable(choices):
            return list(choices())
        return list(choices or [])


@dataclass
class TaskDef:
    """任务定义。"""
    id: str
    name: str
    description: str
    entry: str                       # 'module:attr' 形式的执行入口
    icon: str = "PLAY"
    params: List[TaskParam] = field(default_factory=list)
    group: str = "原神"
    # 持续性任务（自动剧情这类需要一直跑、直到手动停的）在界面上
    # 渲染成「开关」而不是可勾选的卡片
    switch: bool = False

    def build_kwargs(self, values: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {}
        for p in self.params:
            if p.key in values:
                kwargs[p.key] = values[p.key]
        return kwargs


# ---------------------------------------------------------------------------
# 选项构造：账号名 / 秘境名（供 choice 类型参数使用）
# ---------------------------------------------------------------------------

def ys_account_choices() -> List:
    """原神账号选项：[(编号, '账号（队伍名）'), ...]，**只列账号页里勾选启用的**。

    账号名实时读 games/ys/data/账号.json（游戏脚本读的同一份）、
    队伍名实时读 games/ys/data/队伍.json，所以这两处改完（或改了启用状态），
    任务卡片上的下拉选项会跟着更新（不必重启程序）。

    值仍然是**编号** —— 编号是稳定标识，与队伍表一一对应，也是游戏侧取
    账号 / 输出轴的依据。
    """
    from automation_gui.core import account_store, team_store

    options = []
    for item in account_store.enabled_ys_accounts():
        index, account = item["编号"], item["账号"]
        team = team_store.team_name(index)
        options.append((index, f"{account}（{team}）" if team else str(account)))
    return options


def ys_account_name_choices() -> List:
    """原神账号选项（值就是账号本身，**只列启用的**）：[(账号, 账号), ...]。

    登录任务直接把账号字符串传给 ``login_one``，所以改了账号或启用状态后，
    登录用的就是新的那一份 —— 不会出现「序号指向的账号已经变了」的错位问题。
    """
    from automation_gui.core import account_store

    return [(item["账号"], item["账号"]) for item in account_store.enabled_ys_accounts()]


def ys_domain_choices() -> List:
    """圣遗物秘境选项：[(编号, '模板图片名'), ...]。

    读取 games/ys/data/秘境圣遗物.json（游戏脚本读的是同一份文件），
    所以「秘境配置」页改完，任务卡片上的下拉选项也会跟着变。
    """
    from automation_gui.core import domain_store

    options = []
    for key, name in domain_store.load_domains().items():
        try:
            options.append((int(key), name))
        except (TypeError, ValueError):
            continue        # 跳过编号不是数字的脏数据
    return sorted(options, key=lambda item: item[0])


# ---------------------------------------------------------------------------
# 原神任务定义
# ---------------------------------------------------------------------------

YS_TASKS: List[TaskDef] = [
    # 放在最上面：最常用的任务。
    # 账号(zh_num) 决定用哪套输出轴 / 队伍，秘境(num) 决定打哪个本 —— 见 ys_mr.run3。
    TaskDef(
        id="ys_domain",
        name="原神圣遗物秘境",
        description="切副本队伍 + 传送战斗领奖 + 分解圣遗物 + 切回常用队伍",
        entry="games.ys.execute.ys_mr:run3",
        icon="GLOBE",
        group="原神",
        params=[
            TaskParam("zh_num", "账号", "choice", 0, choices=ys_account_choices),
            TaskParam("num", "秘境", "choice", 1, choices=ys_domain_choices),
        ],
    ),
    TaskDef(
        id="ys_daily",
        name="原神每日任务",
        description="登录 + 邮件 + 合成 + 秘境圣遗物 + 分解 + 委托 + 纪行（对应 ys_mr.run）",
        entry="games.ys.execute.ys_mr:run",
        icon="HOME",
        group="原神",
    ),
    TaskDef(
        id="ys_daily2",
        name="原神每日任务2（幽境危战）",
        description="登录 + 邮件 + 合成 + 幽境危战 + 分解 + 委托 + 纪行（对应 ys_mr.run2）",
        entry="games.ys.execute.ys_mr:run2",
        icon="HOME",
        group="原神",
    ),
    TaskDef(
        id="ys_login_all",
        name="原神批量登录",
        description="依次登录所有账号，每个账号登录后等待按下 0 继续（对应 ys_login.logins）",
        entry="games.ys.execute.ys_login:logins",
        icon="PEOPLE",
        group="原神",
    ),
    TaskDef(
        id="ys_login_one",
        name="原神单账号登录",
        description="登录指定账号（对应 ys_login.login_one）；可用快捷键 g+数字 快速触发",
        entry="games.ys.execute.ys_login:login_one",
        icon="PEOPLE",
        group="原神",
        params=[
            TaskParam("n", "账号", "choice", "", choices=ys_account_name_choices),
        ],
    ),
    # 自检任务：跑一遍和「原神单账号登录」完全相同的完整流程，
    # 额外输出一份输入法自检报告（输入语言是否全程英文、有没有新弹输入法窗口），
    # 用来验证「游戏内还会不会弹中文输入法」。跑完在日志页看结论即可。
    TaskDef(
        id="ys_login_check",
        name="原神登录自检（输入法）",
        description="按完整流程登录一次并输出输入法自检报告，判断游戏内还会不会弹中文输入法",
        entry="games.ys.execute.ys_login_check:登录自检",
        icon="PEOPLE",
        group="原神",
        params=[
            TaskParam("account", "账号", "choice", "", choices=ys_account_name_choices),
        ],
    ),
    TaskDef(
        id="ys_talk",
        name="原神自动剧情",
        description="自动点击/跳过剧情对话，按 F9 可开关（对应 ys_talk.ys_talk）",
        entry="games.ys.execute.ys_talk:ys_talk",
        icon="MESSAGE",
        group="原神",
        switch=True,          # 持续任务：界面上是开关（快捷键 +t 也可开/关）
    ),
    TaskDef(
        id="ys_mail",
        name="原神邮件领取",
        description="领取邮件奖励（对应 ys_action.邮件领取）",
        entry="games.ys.action.ys_action:邮件领取",
        icon="MAIL",
        group="原神",
    ),
    TaskDef(
        id="ys_code",
        name="原神兑换码",
        description="批量兑换兑换码（对应 ys_action.兑换码）",
        entry="games.ys.action.ys_action:兑换码",
        icon="GIFT",
        group="原神",
    ),
    TaskDef(
        id="ys_artifact",
        name="原神圣遗物分解",
        description="自动分解圣遗物（对应 ys_action.圣遗物分解）",
        entry="games.ys.action.ys_action:圣遗物分解",
        icon="DELETE",
        group="原神",
    ),
    TaskDef(
        id="ys_achievement",
        name="原神成就领取",
        description="循环领取成就奖励（对应 ys_action.成就领取）",
        entry="games.ys.action.ys_action:成就领取",
        icon="ACCEPT",
        group="原神",
    ),
    TaskDef(
        id="ys_butterfly",
        name="原神晶蝶采集",
        description="自动采集晶蝶（对应 ys_action.晶蝶）",
        entry="games.ys.action.ys_action:晶蝶",
        icon="FLY",
        group="原神",
    ),
]


# ---------------------------------------------------------------------------
# 崩坏：星穹铁道任务定义
# ---------------------------------------------------------------------------

BT_TASKS: List[TaskDef] = [
    TaskDef(
        id="bt_daily",
        name="崩铁每日任务",
        description="登录 + 每日清体力（对应 bt_mr.mr_execute）",
        entry="games.starRail.execute.bt_mr:mr_execute",
        icon="HOME",
        group="崩铁",
    ),
    TaskDef(
        id="bt_login_all",
        name="崩铁批量登录",
        description="依次登录所有账号（对应 bt_login.logins）",
        entry="games.starRail.execute.bt_login:logins",
        icon="PEOPLE",
        group="崩铁",
    ),
    TaskDef(
        id="bt_login_one",
        name="崩铁单账号登录",
        description="登录指定序号的账号（对应 bt_login.login_one）",
        entry="games.starRail.execute.bt_login:login_one",
        icon="PEOPLE",
        group="崩铁",
        params=[
            TaskParam("n", "账号序号", "int", 0, minimum=0, maximum=99),
        ],
    ),
    TaskDef(
        id="bt_talk",
        name="崩铁自动剧情",
        description="自动跳过剧情对话（对应 bt_talk.bt_talk）",
        entry="games.starRail.execute.bt_talk:bt_talk",
        icon="MESSAGE",
        group="崩铁",
        switch=True,          # 持续任务：界面上是开关
    ),
    TaskDef(
        id="bt_auto",
        name="崩铁活动",
        description="自动完成活动（对应 bt_auto.bt_auto）",
        entry="games.starRail.execute.bt_auto:bt_auto",
        icon="GLOBE",
        group="崩铁",
    ),
    TaskDef(
        id="bt_mnyz",
        name="崩铁模拟宇宙",
        description="自动模拟宇宙（对应 bt_mnyz，按 B 键开关）",
        entry="automation_gui.core.wrappers:bt_mnyz_run",
        icon="GLOBE",
        group="崩铁",
    ),
]


# ---------------------------------------------------------------------------
# 鸣潮任务定义
# ---------------------------------------------------------------------------

MC_TASKS: List[TaskDef] = [
    TaskDef(
        id="mc_daily",
        name="鸣潮每日任务",
        description="登录 + 每日清体力（对应 mc_mr.run）",
        entry="games.mc.execute.mc_mr:run",
        icon="HOME",
        group="鸣潮",
    ),
    TaskDef(
        id="mc_talk",
        name="鸣潮自动剧情",
        description="自动跳过剧情对话（对应 mc_jq.mc_talk）",
        entry="games.mc.execute.mc_jq:mc_talk",
        icon="MESSAGE",
        group="鸣潮",
        switch=True,          # 持续任务：界面上是开关
    ),
]


ALL_TASKS: List[TaskDef] = YS_TASKS + BT_TASKS + MC_TASKS


def get_task(task_id: str) -> Optional[TaskDef]:
    for t in ALL_TASKS:
        if t.id == task_id:
            return t
    return None


def tasks_by_group() -> Dict[str, List[TaskDef]]:
    groups: Dict[str, List[TaskDef]] = {}
    for t in ALL_TASKS:
        groups.setdefault(t.group, []).append(t)
    return groups
