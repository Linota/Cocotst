from typing import Optional

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface

from cocotst.config.debug import DebugConfig
from cocotst.event import CocotstBaseEvent


class DebugFlagSetup(CocotstBaseEvent):
    debug_config: Optional[DebugConfig] = None

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["DebugFlagSetup"]):
            if isinstance(interface.event, DebugFlagSetup):
                if interface.annotation == DebugConfig:
                    return interface.event.debug_config
