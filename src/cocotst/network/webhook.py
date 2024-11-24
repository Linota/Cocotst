from creart import it
from graia.broadcast import Broadcast
from launart import Launart
from loguru import logger
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from cocotst.event.message import C2CMessage, GroupMessage, MessageEvent
from cocotst.network.model import Content, Group, Member, Payload
from cocotst.network.services import QAuth
from cocotst.network.sign import sign

broadcast = it(Broadcast)


async def postevent(request):
    data = await request.json()

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

        broadcast.postEvent(payload)
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


app = Starlette(
    debug=True,
    routes=[
        Route("/postevent", postevent, methods=["POST"]),
    ],
)
