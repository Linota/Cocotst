import launart
from cocotst.network.services import HttpxClientSessionService


async def httpx(safe: bool = False):
    if safe:
        return launart.Launart.current().get_component(HttpxClientSessionService).async_client_safe
    else:
        return launart.Launart.current().get_component(HttpxClientSessionService).async_client
