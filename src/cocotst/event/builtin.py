from typing import Optional

from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from pydantic import BaseModel

from cocotst.config import DebugConfig


class DebugFlagSetup(BaseModel):
    debug_config: Optional[DebugConfig] = None

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface["DebugFlagSetup"]):
            if isinstance(interface.event, DebugFlagSetup):
                if interface.annotation == DebugConfig:
                    return interface.event.debug_config
