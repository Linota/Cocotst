from typing import Optional

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel

from cocotst.network.model import Target


class GroupDelRobot(BaseModel):
    """群删除机器人"""

    id: str
    """事件 ID"""
    timestamp: int
    """事件触发时间"""
    group_openid: str
    """群 openid"""
    op_member_openid: str
    """操作者 openid"""

    @property
    def target(self):
        return Target(target_unit=self.group_openid, event_id=self.id)


class GroupAddRobot(BaseModel):
    """群添加机器人"""

    id: str
    """事件 ID"""
    timestamp: int
    """事件触发时间"""
    group_openid: str
    """群 openid"""
    op_member_openid: str
    """操作者 openid"""

    @property
    def target(self):
        return Target(target_unit=self.group_openid, event_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["GroupAddRobot"]):
            if isinstance(interface.event, GroupAddRobot):
                if interface.annotation == Target:
                    return interface.event.target


class FriendAdd(BaseModel):
    """好友添加"""

    id: str
    """事件 ID"""
    user_openid: str
    """用户 openid"""
    timestamp: int
    """事件触发时间"""

    @property
    def target(self):
        return Target(target_unit=self.user_openid, event_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["FriendAdd"]):
            if isinstance(interface.event, FriendAdd):
                if interface.annotation == Target:
                    return interface.event.target


class FriendDel(BaseModel):
    """好友删除"""

    id: str
    """事件 ID"""
    user_openid: str
    """用户 openid"""
    timestamp: int
    """事件触发时间"""

    @property
    def target(self):
        return Target(target_unit=self.user_openid, event_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["FriendDel"]):
            if isinstance(interface.event, FriendDel):
                if interface.annotation == Target:
                    return interface.event.target
