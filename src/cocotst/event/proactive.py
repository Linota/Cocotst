from typing import Optional

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface

from cocotst.network.model.target import Target
from cocotst.event import CocotstBaseEvent

class GroupAllowBotProactiveMessage(CocotstBaseEvent):
    """群打开消息推送"""

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
        async def catch(interface: DispatcherInterface["GroupAllowBotProactiveMessage"]):
            if isinstance(interface.event, GroupAllowBotProactiveMessage):
                if interface.annotation == Target:
                    return interface.event.target


class GroupRejectBotProactiveMessage(CocotstBaseEvent):
    """群关闭消息推送"""

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
        async def catch(interface: DispatcherInterface["GroupRejectBotProactiveMessage"]):
            if isinstance(interface.event, GroupRejectBotProactiveMessage):
                if interface.annotation == Target:
                    return interface.event.target


class C2CAllowBotProactiveMessage(CocotstBaseEvent):
    """C2C 打开消息推送"""

    id: str
    """事件 ID"""
    timestamp: int
    """事件触发时间"""
    user_openid: str
    """用户 openid"""

    @property
    def target(self):
        return Target(target_unit=self.user_openid, event_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["C2CAllowBotProactiveMessage"]):
            if isinstance(interface.event, C2CAllowBotProactiveMessage):
                if interface.annotation == Target:
                    return interface.event.target


class C2CRejectBotProactiveMessage(CocotstBaseEvent):
    """C2C 关闭消息推送"""

    id: str
    """事件 ID"""
    timestamp: int
    """事件触发时间"""
    user_openid: str
    """用户 openid"""

    @property
    def target(self):
        return Target(target_unit=self.user_openid, event_id=self.id)

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["C2CRejectBotProactiveMessage"]):
            if isinstance(interface.event, C2CRejectBotProactiveMessage):
                if interface.annotation == Target:
                    return interface.event.target
