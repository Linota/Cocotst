import json

from creart import it
from graia.broadcast import Broadcast
from launart import Launart
from loguru import logger
from starlette.responses import JSONResponse

from cocotst.config import DebugFlag
from cocotst.event.builtin import DebugFlagSetup
from cocotst.event.message import C2CMessage, GroupMessage
from cocotst.event.receive import GroupAllowReceive, GroupRejectReceive
from cocotst.event.robot import FriendAdd, FriendDel, GroupAddRobot, GroupDelRobot
from cocotst.network.model import Content, Group, Member, Payload
from cocotst.network.services import QAuth
from cocotst.network.sign import sign

broadcast = it(Broadcast)

debug_flag = DebugFlag()


@broadcast.receiver(DebugFlagSetup)
async def debug_flag_setup(event: DebugFlagSetup):
    debug_flag.debug_config = event.debug_config
    debug_flag.debug_flag = True
    debug_flag.checked_debug_flags = True


async def postevent(request):
    data = await request.json()
    if debug_flag.debug_flag:
        if debug_flag.debug_config.webhook.print_webhook_data:
            logger.debug(f"[DEBUG] Webhook data:\n{json.dumps(data, indent=4)}")
    op = data["op"]
    if op == 0:
        payload = Payload(**data)
        if payload.t == "GROUP_AT_MESSAGE_CREATE":
            event = GroupMessage(
                id=payload.d.id,
                content=Content(payload.d.content),
                timestamp=payload.d.timestamp,
                author=payload.d.author,
                message_scene=payload.d.message_scene,
                group=Group(group_id=payload.d.group_id, group_openid=payload.d.group_openid),
                member=Member(member_openid=payload.d.author.member_openid),
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] GroupMessage: {}", event.id)
        elif payload.t == "C2C_MESSAGE_CREATE":
            event = C2CMessage(
                id=payload.d.id,
                content=Content(payload.d.content),
                timestamp=payload.d.timestamp,
                author=payload.d.author,
                message_scene=payload.d.message_scene,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] C2CMessage: {}", event.id)
        elif payload.t == "GROUP_MSG_RECEIVE":
            event = GroupAllowReceive(
                id=payload.id,
                timestamp=payload.d.timestamp,
                group_openid=payload.d.group_openid,
                op_member_openid=payload.d.op_member_openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] GroupAllowReceive: {}", event.id)
        elif payload.t == "GROUP_MSG_REJECT":
            event = GroupRejectReceive(
                id=payload.id,
                timestamp=payload.d.timestamp,
                group_openid=payload.d.group_openid,
                op_member_openid=payload.d.op_member_openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] GroupRejectReceive: {}", event.id)
        elif payload.t == "GROUP_ADD_ROBOT":
            event = GroupAddRobot(
                id=payload.id,
                timestamp=payload.d.timestamp,
                group_openid=payload.d.group_openid,
                op_member_openid=payload.d.op_member_openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] GroupAddRobot: {}", event.id)
        elif payload.t == "GROUP_DEL_ROBOT":
            event = GroupDelRobot(
                id=payload.id,
                timestamp=payload.d.timestamp,
                group_openid=payload.d.group_openid,
                op_member_openid=payload.d.op_member_openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] GroupDelRobot: {}", event.id)
        elif payload.t == "FRIEND_ADD":
            event = FriendAdd(
                id=payload.id,
                timestamp=payload.d.timestamp,
                user_openid=payload.d.openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] FriendAdd: {}", event.id)
        elif payload.t == "FRIEND_DEL":
            event = FriendDel(
                id=payload.id,
                timestamp=payload.d.timestamp,
                user_openid=payload.d.openid,
            )
            broadcast.postEvent(event)
            logger.info("[RECIEVE] FriendDel: {}", event.id)

        return JSONResponse({"status": "ok"})

    elif op == 13:
        mgr = it(Launart)
        qauth = mgr.get_component(QAuth)
        secret = qauth.clientSecret
        event_ts = data["d"]["event_ts"]
        plain_token = data["d"]["plain_token"]
        signature = sign(secret, event_ts + plain_token)
        return JSONResponse({"plain_token": plain_token, "signature": signature})

    else:
        print(data)
        return JSONResponse({"error": "Invalid operation"}, status_code=400)
