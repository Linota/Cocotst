from creart import it
from graia.broadcast import Broadcast
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from launart import Launart, Service
from loguru import logger

from cocotst.app import Cocotst


class CocotstDispatcher(BaseDispatcher):
    """
    App Dispatcher.
    """

    @staticmethod
    async def catch(interface: DispatcherInterface):
        if interface.annotation == Cocotst:
            mgr = it(Launart)
            return mgr.get_component(App).app


class App(Service):
    """
    App Service.
    """

    id = "Cocotst"
    app: Cocotst

    @property
    def stages(self):
        return {"preparing", "blocking", "cleanup"}

    @property
    def required(self):
        return set()

    def __init__(self, app: Cocotst):
        self.app = app
        super().__init__()

    async def launch(self, manager):
        async with self.stage("preparing"):
            logger.info("[APP] Inject Dispatchers")
            broadcast = it(Broadcast)
            broadcast.finale_dispatchers.append(CocotstDispatcher())
            logger.info("[APP] Injected Dispatchers")

        async with self.stage("blocking"):
            pass

        async with self.stage("cleanup"):
            pass
