from typing import Optional, Union

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel, RootModel


class Author(BaseModel):
    """消息发送者"""

    id: Optional[str] = None
    member_openid: Optional[str] = None
    user_openid: Optional[str] = None
    union_openid: Optional[str] = None


class MessageScene(BaseModel):
    """消息场景"""

    source: str


class D(BaseModel):
    """基础数据"""

    id: Optional[str] = None
    """消息 ID，被动回复消息时请使用此字段"""
    timestamp: Optional[Union[str, int]] = None
    group_id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[Author] = None
    group_openid: Optional[str] = None
    message_scene: Optional[MessageScene] = None
    op_member_openid: Optional[str] = None
    """操作者的 openid, 仅在群消息中有效, 用于区分是谁操作关闭开启群消息推送"""
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


class Group(BaseModel):
    """群组信息"""

    group_id: str
    group_openid: str

    @property
    def target(self):
        return Target(target_unit=self.group_openid)


class Member(BaseModel):
    """群成员信息"""

    member_openid: str


class Content(RootModel[str]):
    """消息内容"""

    @property
    def content(self):
        return self.root


class Target(BaseModel):
    """回复目标"""

    target_unit: Optional[str] = None
    """精确的 openid , 群消息的时候是群的 openid , 私聊消息的时候是用户的 openid"""
    target_id: Optional[str] = None
    """被动回复消息的时候需要的消息 id"""
    event_id: Optional[str] = None
    """非用户主动事件触发的时候需要的 event_id"""


class WebHookConfig(BaseModel):
    """webhook 配置"""

    host: str = "0.0.0.0"
    """webhook 的 host"""
    port: int = 2077
    """webhook 的 port"""
    postevent: str = "/postevent"
    """webhook 的 postevent url"""


class FileServerConfig(BaseModel):
    localpath: str = None
    """本地文件路径"""
    remote_url: str = "/fileserver"
    """远程文件路径"""


class AccessToken(BaseModel):
    access_token: str
    expires_in: int
