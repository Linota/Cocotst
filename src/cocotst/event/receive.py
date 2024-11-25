from typing import Optional

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel

from cocotst.network.model import Target


class GroupAllowReceive(BaseModel):
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
        async def catch(interface: DispatcherInterface["GroupAllowReceive"]):
            if isinstance(interface.event, GroupAllowReceive):
                if interface.annotation == Target:
                    return interface.event.target


class GroupRejectReceive(BaseModel):
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
        async def catch(interface: DispatcherInterface["GroupRejectReceive"]):
            if isinstance(interface.event, GroupRejectReceive):
                if interface.annotation == Target:
                    return interface.event.target
