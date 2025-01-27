import json
from typing import Optional, Dict, Any, Callable
from functools import partial
from dataclasses import dataclass

from creart import it
from graia.broadcast import Broadcast
from launart import Launart
from loguru import logger
from starlette.responses import JSONResponse

from cocotst.config.debug import DebugFlag
from cocotst.event.builtin import DebugFlagSetup
from cocotst.event.message import C2CMessage, ChannelMessage, GroupMessage
from cocotst.event.proactive import (
    C2CAllowBotProactiveMessage,
    C2CRejectBotProactiveMessage,
    GroupAllowBotProactiveMessage,
    GroupRejectBotProactiveMessage,
)
from cocotst.event.robot import FriendAdd, FriendDel, GroupAddRobot, GroupDelRobot
from cocotst.network.model.event_element.normal import Group, Member
from cocotst.network.model.webhook import Content, Payload
from cocotst.network.services import QAuth
from cocotst.network.sign import sign
from cocotst.utils.guild import handle_text

# 全局实例
broadcast = it(Broadcast)
debug_flag = DebugFlag()


class PayloadPath:
    """Payload 数据路径常量类,用于提高可维护性和减少错误"""

    # 基础路径
    ROOT = ""  # 根路径
    DATA = "d"  # 数据路径

    # ID和时间戳
    MESSAGE_ID = "d.id"
    TIMESTAMP = "d.timestamp"

    # 消息内容相关
    CONTENT = "d.content"
    ATTACHMENTS = "d.attachments"
    MENTIONS = "d.mentions"
    MESSAGE_SCENE = "d.message_scene"

    # 作者相关
    AUTHOR = "d.author"
    MEMBER = "d.member"
    MEMBER_OPENID = "d.author.member_openid"

    # 群组相关
    GROUP_ID = "d.group_id"
    GROUP_OPENID = "d.group_openid"
    OP_MEMBER_OPENID = "d.op_member_openid"

    # 频道相关
    CHANNEL_ID = "d.channel_id"
    GUILD_ID = "d.guild_id"
    SEQ = "d.seq"
    SEQ_IN_CHANNEL = "d.seq_in_channel"

    # C2C相关
    USER_OPENID = "d.openid"

    # 特殊标记,用于自定义处理
    SPECIAL_GROUP = "__special_group__"
    SPECIAL_MEMBER = "__special_member__"


@dataclass
class EventConfig:
    """事件配置类,用于统一事件处理的参数映射"""

    event_class: type  # 事件类
    log_category: str  # 日志分类
    event_params: Dict[str, str]  # 参数映射 {'目标参数名': '源数据路径'}


def analyze_event_tree(event) -> None:
    """使用树形结构分析并记录事件的详细信息"""

    def log_tree(prefix: str, name: str, value: Any, level: int = 0) -> None:
        """递归生成树形日志"""
        indent = "    " * level
        if isinstance(value, (str, int, float, bool)) or value is None:
            logger.info(f"{prefix}{indent}├─ {name}: {value}")
        elif isinstance(value, (list, tuple)):
            logger.info(f"{prefix}{indent}├─ {name}: [")
            for i, item in enumerate(value):
                if isinstance(item, (dict, list, tuple)) or hasattr(item, "__dict__"):
                    logger.info(f"{prefix}{indent}│  ├─ 项目 {i}:")
                    log_tree(prefix, "", item, level + 2)
                else:
                    logger.info(f"{prefix}{indent}│  ├─ 项目 {i}: {item}")
            logger.info(f"{prefix}{indent}│  ]")
        elif hasattr(value, "__dict__"):
            logger.info(f"{prefix}{indent}├─ {name}:")
            for attr_name, attr_value in value.__dict__.items():
                if not attr_name.startswith("_"):  # 跳过私有属性
                    log_tree(prefix, attr_name, attr_value, level + 1)

    # 开始分析事件
    event_type = event.__class__.__name__
    logger.info(f"\n[事件分析] {'='*20} {event_type} {'='*20}")

    # 根据不同事件类型进行专门的分析
    if isinstance(event, GroupMessage):
        logger.info("┌─ 群聊消息事件")
        log_tree("│", "消息ID", event.id)
        log_tree("│", "时间戳", event.timestamp)
        log_tree("│", "消息内容", event.content)
        log_tree("│", "群组信息", event.group)
        log_tree("│", "发送者", event.member)
        log_tree("│", "消息场景", event.message_scene)

    elif isinstance(event, C2CMessage):
        logger.info("┌─ 私聊消息事件")
        log_tree("│", "消息ID", event.id)
        log_tree("│", "时间戳", event.timestamp)
        log_tree("│", "消息内容", event.content)
        log_tree("│", "发送者", event.author)
        log_tree("│", "消息场景", event.message_scene)
        log_tree("│", "附件", event.attachments)

    elif isinstance(event, ChannelMessage):
        logger.info("┌─ 频道消息事件")
        log_tree("│", "消息ID", event.id)
        log_tree("│", "时间戳", event.timestamp)
        log_tree("│", "频道ID", event.channel_id)
        log_tree("│", "服务器ID", event.guild_id)
        log_tree("│", "消息内容", event.content)
        log_tree("│", "发送者", event.author)
        log_tree("│", "成员信息", event.member)
        log_tree("│", "提及用户", event.mentions)
        log_tree("│", "附件", event.attachments)
        log_tree("│", "消息序号", event.seq)
        log_tree("│", "频道内序号", event.seq_in_channel)

    elif isinstance(event, (GroupAddRobot, GroupDelRobot)):
        logger.info(f"┌─ 机器人{'入群' if isinstance(event, GroupAddRobot) else '退群'}事件")
        log_tree("│", "事件ID", event.id)
        log_tree("│", "时间戳", event.timestamp)
        log_tree("│", "群组OpenID", event.group_openid)
        log_tree("│", "操作成员OpenID", event.op_member_openid)

    elif isinstance(event, (FriendAdd, FriendDel)):
        logger.info(f"┌─ 好友{'添加' if isinstance(event, FriendAdd) else '删除'}事件")
        log_tree("│", "事件ID", event.id)
        log_tree("│", "时间戳", event.timestamp)
        log_tree("│", "用户OpenID", event.user_openid)

    logger.info(f"[事件分析] {'='*50}")


# 修改 create_event 函数，在返回事件前进行分析
def create_event(payload: Payload, config: EventConfig):
    """统一的事件创建函数"""
    logger.info(f"[Webhook][{config.log_category}] 开始处理事件")

    # 原有的事件创建逻辑
    event_args = {}
    for target_param, source_path in config.event_params.items():
        if source_path == PayloadPath.SPECIAL_GROUP:
            event_args[target_param] = Group(group_id=payload.d.group_id, group_openid=payload.d.group_openid)
        elif source_path == PayloadPath.SPECIAL_MEMBER:
            event_args[target_param] = Member(member_openid=payload.d.author.member_openid)
        else:
            value = payload
            for key in source_path.split("."):
                value = getattr(value, key)
            event_args[target_param] = value

    if "content" in event_args:
        event_args["content"] = Content(event_args["content"])

    event = config.event_class(**event_args)

    # 添加事件分析
    analyze_event_tree(event)

    logger.info(f"[Webhook][{config.log_category}] 事件处理完成")
    return event


# 统一的事件配置,使用常量路径
EVENT_CONFIGS = {
    "GROUP_AT_MESSAGE_CREATE": EventConfig(
        event_class=GroupMessage,
        log_category="群聊消息",
        event_params={
            "id": PayloadPath.MESSAGE_ID,
            "content": PayloadPath.CONTENT,
            "timestamp": PayloadPath.TIMESTAMP,
            "author": PayloadPath.AUTHOR,
            "message_scene": PayloadPath.MESSAGE_SCENE,
            "group": PayloadPath.SPECIAL_GROUP,
            "member": PayloadPath.SPECIAL_MEMBER,
        },
    ),
    "C2C_MESSAGE_CREATE": EventConfig(
        event_class=C2CMessage,
        log_category="私聊消息",
        event_params={
            "id": PayloadPath.MESSAGE_ID,
            "content": PayloadPath.CONTENT,
            "timestamp": PayloadPath.TIMESTAMP,
            "author": PayloadPath.AUTHOR,
            "message_scene": PayloadPath.MESSAGE_SCENE,
            "attachments": PayloadPath.ATTACHMENTS,
        },
    ),
    "AT_MESSAGE_CREATE": EventConfig(
        event_class=ChannelMessage,
        log_category="频道消息",
        event_params={
            "id": PayloadPath.MESSAGE_ID,
            "content": PayloadPath.CONTENT,
            "timestamp": PayloadPath.TIMESTAMP,
            "author": PayloadPath.AUTHOR,
            "channel_id": PayloadPath.CHANNEL_ID,
            "guild_id": PayloadPath.GUILD_ID,
            "attachments": PayloadPath.ATTACHMENTS,
            "mentions": PayloadPath.MENTIONS,
            "seq": PayloadPath.SEQ,
            "seq_in_channel": PayloadPath.SEQ_IN_CHANNEL,
            "member": PayloadPath.MEMBER,
        },
    ),
    "GROUP_MSG_RECEIVE": EventConfig(
        event_class=GroupAllowBotProactiveMessage,
        log_category="群消息接收许可",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "group_openid": PayloadPath.GROUP_OPENID,
            "op_member_openid": PayloadPath.OP_MEMBER_OPENID,
        },
    ),
    "GROUP_MSG_REJECT": EventConfig(
        event_class=GroupRejectBotProactiveMessage,
        log_category="群消息接收拒绝",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "group_openid": PayloadPath.GROUP_OPENID,
            "op_member_openid": PayloadPath.OP_MEMBER_OPENID,
        },
    ),
    "C2C_MSG_REJECT": EventConfig(
        event_class=C2CRejectBotProactiveMessage,
        log_category="私聊消息拒绝",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "user_openid": PayloadPath.USER_OPENID,
        },
    ),
    "C2C_MSG_RECEIVE": EventConfig(
        event_class=C2CAllowBotProactiveMessage,
        log_category="私聊消息接收",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "user_openid": PayloadPath.USER_OPENID,
        },
    ),
    "GROUP_ADD_ROBOT": EventConfig(
        event_class=GroupAddRobot,
        log_category="机器人入群",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "group_openid": PayloadPath.GROUP_OPENID,
            "op_member_openid": PayloadPath.OP_MEMBER_OPENID,
        },
    ),
    "GROUP_DEL_ROBOT": EventConfig(
        event_class=GroupDelRobot,
        log_category="机器人退群",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "group_openid": PayloadPath.GROUP_OPENID,
            "op_member_openid": PayloadPath.OP_MEMBER_OPENID,
        },
    ),
    "FRIEND_ADD": EventConfig(
        event_class=FriendAdd,
        log_category="好友添加",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "user_openid": PayloadPath.USER_OPENID,
        },
    ),
    "FRIEND_DEL": EventConfig(
        event_class=FriendDel,
        log_category="好友删除",
        event_params={
            "id": PayloadPath.ROOT + "id",
            "timestamp": PayloadPath.TIMESTAMP,
            "user_openid": PayloadPath.USER_OPENID,
        },
    ),
}

# 通过配置生成处理器
EVENT_HANDLERS = {
    event_type: lambda p, cfg=config: create_event(p, cfg) for event_type, config in EVENT_CONFIGS.items()
}


async def handle_signature_verify(data: Dict) -> JSONResponse:
    """处理签名验证请求"""
    try:
        logger.info("[Webhook][签名验证] 开始处理签名验证请求")
        mgr = it(Launart)
        qauth = mgr.get_component(QAuth)
        secret = qauth.clientSecret
        event_ts = data["d"]["event_ts"]
        plain_token = data["d"]["plain_token"]
        signature = sign(secret, event_ts + plain_token)

        logger.info("[Webhook][签名验证] 签名验证成功")
        return JSONResponse({"plain_token": plain_token, "signature": signature})
    except Exception as e:
        logger.error(f"[Webhook][签名验证] 验证失败: {str(e)}")
        return JSONResponse({"error": "签名验证失败"}, status_code=500)


@broadcast.receiver(DebugFlagSetup)
async def debug_flag_setup(event: DebugFlagSetup):
    """处理调试标志设置"""
    debug_flag.debug_config = event.debug_config
    debug_flag.debug_flag = True
    debug_flag.checked_debug_flags = True


async def postevent(request):
    """处理 Webhook 请求的主入口"""
    try:
        data = await request.json()
        logger.info("[Webhook] 收到新的 Webhook 请求")

        if debug_flag.debug_flag and debug_flag.debug_config.webhook.print_webhook_data:
            logger.info("[Webhook][调试] 请求数据:")
            print(json.dumps(data, indent=4, ensure_ascii=False))

        op = data["op"]

        if op == 0:
            payload = Payload(**data)
            event_type = payload.t

            handler = EVENT_HANDLERS.get(event_type)
            if handler:
                event = handler(payload)
                broadcast.postEvent(event)
                logger.info(f"[Webhook] 事件处理完成并推送: [{event.__class__.__name__}]")
                return JSONResponse({"status": "ok"})
            else:
                logger.warning(f"[Webhook] 未知的事件类型: [{event_type}]")
                return JSONResponse({"error": "未知的事件类型"}, status_code=400)

        elif op == 13:
            return await handle_signature_verify(data)

        else:
            logger.warning(f"[Webhook] 收到未知操作类型: [{op}]")
            return JSONResponse({"error": "无效的操作类型"}, status_code=400)

    except Exception as e:
        logger.error(f"[Webhook] 处理请求时发生错误: {str(e)}")
        return JSONResponse({"error": "内部服务器错误"}, status_code=500)
