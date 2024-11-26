from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel

from cocotst.network.model import Author, Content, Group, Member, MessageScene, Target


class MessageEvent(BaseModel):
    """消息事件"""

    id: str
    content: Content
    """消息文字内容"""
    timestamp: str
    """消息发送时间"""
    author: Author
    """消息发送者"""
    message_scene: MessageScene
    """消息场景"""

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["MessageEvent"]):
            if isinstance(interface.event, MessageEvent):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Author:
                    return interface.event.author


class GroupMessage(MessageEvent):
    """群消息事件"""

    group: Group
    """群信息"""
    member: Member
    """群成员信息"""

    @property
    def target(self):
        """快速回复目标"""
        return Target(target_unit=self.group.group_openid, target_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["GroupMessage"]):
            if isinstance(interface.event, GroupMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Group:
                    return interface.event.group
                if interface.annotation == Member:
                    return interface.event.member
                if interface.annotation == Target:
                    return interface.event.target


class C2CMessage(MessageEvent):
    @property
    def target(self):
        """快速回复目标"""
        return Target(target_unit=self.author.user_openid, target_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["C2CMessage"]):
            if isinstance(interface.event, C2CMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Author:
                    return interface.event.author
                if interface.annotation == Target:
                    return interface.event.target
