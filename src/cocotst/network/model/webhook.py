# 本文件定义了 cocotst 网络模块的通用数据模型

from typing import List, Optional, Union
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel, RootModel
from cocotst.network.model.event_element.guild import  Mention, Member as GuildMember
from cocotst.network.model.event_element.normal import Group, Member as GroupMember, MessageScene
from cocotst.network.model.event_element import Attachments

class Author(BaseModel):
    """消息发送者"""

    # 以下字段为常规聊天和频道共用字段
    id: Optional[str] = None
    union_openid: Optional[str] = None

    # 以下字段为频道专有字段
    username: Optional[str] = None
    avatar: Optional[str] = None
    bot: Optional[bool] = None

    # 以下字段为群专有字段
    member_openid: Optional[str] = None

    # 以下字段为 C2C 专有字段
    user_openid: Optional[str] = None

    def ensure_avatar(self):
        if not self.avatar:
            if self.member_openid:
                self.avatar = f"https://q.qlogo.cn/qqapp/102130931/{self.member_openid}/640"
            elif self.user_openid:
                self.avatar = f"https://q.qlogo.cn/qqapp/102130931/{self.user_openid}/640"




class D(BaseModel):
    """基础数据"""

    # 以下字段为常规聊天和频道共用字段
    id: Optional[str] = None
    """消息 ID，被动回复消息时请使用此字段"""
    timestamp: Optional[Union[str, int]] = None
    content: Optional[str] = None
    author: Optional[Author] = None
    member: Optional[Union[GroupMember, GuildMember]] = None

    # Guild 专有字段
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[Author] = None
    attachments: Optional[Attachments] = None
    mentions: Optional[List[Mention]] = None
    seq: Optional[int] = None
    seq_in_channel: Optional[int] = None
    # Normal 专有字段
    message_scene: Optional[MessageScene] = None

    # 以下字段为群专有字段
    group_id: Optional[str] = None
    op_member_openid: Optional[str] = None
    """操作者的 openid, 仅在群消息中有效, 用于区分是谁操作关闭开启群消息推送"""
    group_openid: Optional[str] = None
    
    # 以下字段为 C2C 专有字段
    openid: Optional[str] = None
    """用户的 openid, 仅在 C2C 中有效, 用于处理 C2C 事件"""


class Payload(BaseModel):
    """消息载体"""

    op: int
    id: str
    """事件 ID，用于事件触发的被动回复"""
    d: D
    t: str

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["Payload"]):
            if interface.annotation == Payload:
                return interface.event


class Content(RootModel[str]):
    """消息内容"""

    @property
    def content(self):
        return self.root
    







