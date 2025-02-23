from typing import List, Optional
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from graia.broadcast.exceptions import ExecutionStop

from cocotst.network.model.webhook import Attachments, Author, Content, Group, MessageScene
from cocotst.network.model.target import Target
from cocotst.network.model.event_element.normal import Member as GroupMember
from cocotst.network.model.event_element.guild import Member as GuildMember, Mention
from cocotst.network.model.event_element import Attachments
from cocotst.event import CocotstBaseEvent


class MessageEvent(CocotstBaseEvent):
    """消息事件"""

    id: str
    content: Content
    """消息文字内容"""
    timestamp: str
    """消息发送时间"""
    author: Author
    """消息发送者"""
    message_scene: Optional[MessageScene] = None
    """消息场景"""

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["MessageEvent"]):  # type: ignore
            if isinstance(interface.event, GroupMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Group:
                    return interface.event.group
                if interface.annotation == GroupMember:
                    return interface.event.member
                if interface.annotation == Target:
                    return interface.event.target
                if interface.annotation == Attachments:
                    if interface.event.attachments is None:
                        raise ExecutionStop
                    return interface.event.attachments

            if isinstance(interface.event, DirectMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Author:
                    return interface.event.author
                if interface.annotation == Target:
                    return interface.event.target
                if interface.annotation == Attachments:
                    if interface.event.attachments is None:
                        raise ExecutionStop
                    return interface.event.attachments
            if isinstance(interface.event, C2CMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Author:
                    return interface.event.author
                if interface.annotation == Target:
                    return interface.event.target
                if interface.annotation == Attachments:
                    if interface.event.attachments is None:
                        raise ExecutionStop
                    return interface.event.attachments
            if isinstance(interface.event, ChannelMessage):
                if interface.annotation == Content:
                    return interface.event.content
                if interface.annotation == Author:
                    return interface.event.author
                if interface.annotation == Target:
                    return interface.event.target
                if interface.annotation == Attachments:
                    if interface.event.attachments is None:
                        raise ExecutionStop
                    return interface.event.attachments

    @property
    def target(self) -> Target:
        """快速回复目标"""
        raise NotImplementedError


class GroupMessage(MessageEvent):
    """群消息事件"""

    group: Group
    """群信息"""
    member: GroupMember
    """群成员信息"""
    attachments: Optional[Attachments] = None

    @property
    def target(self):
        """快速回复目标"""
        return Target(target_unit=self.group.group_openid, target_id=self.id)


class C2CMessage(MessageEvent):
    """C2C 消息事件"""

    attachments: Optional[Attachments] = None
    """附件信息"""

    @property
    def target(self):
        """快速回复目标"""
        assert self.author.user_openid
        return Target(target_unit=self.author.user_openid, target_id=self.id)


class ChannelMessage(MessageEvent):
    """子频道消息事件"""

    channel_id: str
    """子频道 ID"""
    guild_id: str
    """服务器(大频道) ID"""
    mentions: List[Mention]
    """@ 对象信息"""
    member: GuildMember
    """服务器成员信息"""
    attachments: Optional[Attachments] = None
    """附件信息"""
    seq: int
    """消息序号"""
    seq_in_channel: int
    """子频道消息序号"""

    @property
    def target(self):
        """快速回复目标"""
        return Target(target_unit=self.channel_id, target_id=self.id)


class DirectMessage(MessageEvent):
    """频道私聊消息事件"""

    channel_id: str
    """子频道 ID"""
    guild_id: str
    """服务器(大频道) ID"""
    member: GuildMember
    """服务器成员信息"""
    attachments: Optional[Attachments] = None
    """附件信息"""
    seq: int
    """消息序号"""
    seq_in_channel: int
    """子频道消息序号"""
    direct_message: bool
    """是否为私聊消息"""
    src_guild_id: str
    """源服务器 ID"""

    @property
    def target(self):
        """快速回复目标"""
        return Target(target_unit=self.guild_id, target_id=self.id)


class MessageSent(CocotstBaseEvent):
    """消息发送事件"""

    id: str
    """消息 ID"""
    timestamp: str
    """消息发送时间"""

    class Dispatcher(BaseDispatcher): ...
