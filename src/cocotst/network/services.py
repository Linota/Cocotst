import asyncio
import contextlib
from typing import cast

import requests
from aiohttp import ClientSession, ClientTimeout
from launart import Launart, Service
from loguru import logger
from uvicorn.config import Config
from uvicorn.server import Server
from aiohttp import ClientSession
from aiohttp.connector import TCPConnector
import ssl


from cocotst.network.model.http_api import AccessToken

ssl_ctx = ssl.create_default_context()
ssl_ctx.set_ciphers("DEFAULT")


def auth(appid: str, clientSecret: str) -> AccessToken:
    """
    获取QQ机器人平台的访问令牌

    Args:
        appid: QQ开放平台应用ID
        clientSecret: QQ开放平台应用密钥

    Returns:
        AccessToken: 包含访问令牌信息的数据模型

    Raises:
        KeyError: 当获取令牌失败时抛出异常
    """
    try:
        response = requests.post(
            "https://bots.qq.com/app/getAppAccessToken",
            json={"appId": appid, "clientSecret": clientSecret},
        )
        response.raise_for_status()
        return AccessToken.model_validate(response.json())
    except Exception as e:
        logger.error("[QQ] 令牌获取失败: {}", str(e), style="bold red")
        raise KeyError(f"获取访问令牌失败: {e}")


class UvicornService(Service):
    """Uvicorn服务"""

    id = "UvicornService"

    def __init__(self, config: Config = None):
        self.config = config
        super().__init__()

    @property
    def stages(self):
        return {"preparing", "blocking", "cleanup"}

    @property
    def required(self):
        return set()

    async def launch(self, mgr: Launart):
        server = Server(config=self.config)

        async with self.stage("preparing"):
            logger.info("[Server] 启动服务中", style="bold blue")

        async with self.stage("blocking"):
            server_task = asyncio.create_task(server.serve())
            await mgr.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                logger.info("[Server] 服务已停止", style="bold blue")


class AiohttpClientSessionService(Service):
    """Aiohttp客户端服务，此服务不被 QAuth 以及 QQAPI 所依赖，且此服务使用 TLS 堆栈默认安全设置"""

    id = "http.client/aiohttp"
    session: ClientSession

    def __init__(self, session: ClientSession | None = None) -> None:
        self.session = cast(ClientSession, session)
        super().__init__()

    @property
    def stages(self):
        return {"preparing", "cleanup"}

    @property
    def required(self):
        return set()

    async def launch(self, _: Launart):
        async with self.stage("preparing"):
            if self.session is None:
                connector = TCPConnector(ssl_context=ssl_ctx)
                self.session = ClientSession(timeout=ClientTimeout(total=None), connector=connector)
        async with self.stage("cleanup"):
            await self.session.close()


class QAuth(Service):
    """循环鉴权服务"""

    id = "QAuth"
    appid: str
    clientSecret: str

    @property
    def stages(self):
        return {"preparing", "blocking", "cleanup"}

    @property
    def required(self):
        return set()

    def __init__(self, appid: str, clientSecret: str):
        self.appid = appid
        self.clientSecret = clientSecret
        super().__init__()

    async def auth_async(self, mgr: Launart, appid: str, clientSecret: str):
        while True:
            await asyncio.sleep(int(self.access_token.expires_in))
            logger.info("[QQ] 正在刷新令牌", style="bold blue")

            async with ClientSession() as session:
                async with session.post(
                    "https://bots.qq.com/app/getAppAccessToken",
                    json={"appId": appid, "clientSecret": clientSecret},
                ) as resp:
                    resp.raise_for_status()
                    self.access_token = AccessToken.model_validate(await resp.json())

            logger.success("[QQ] 令牌刷新成功", style="bold green")
            logger.info("[QQ] 下一次令牌刷新时间: {}", self.access_token.expires_in, style="bold blue")

    async def launch(self, mgr: Launart):
        async with self.stage("preparing"):
            logger.info("[QQ] 正在获取首次令牌", style="bold blue")
            self.access_token = auth(self.appid, self.clientSecret)
            logger.success("[QQ] 首次令牌获取成功", style="bold green")
            logger.info("[QQ] 下一次令牌刷新时间: {}", self.access_token.expires_in, style="bold blue")

        async with self.stage("blocking"):
            refresh_task = asyncio.create_task(self.auth_async(mgr, self.appid, self.clientSecret))
            await mgr.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            refresh_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await refresh_task
            logger.info("[QQ] 认证服务已停止", style="bold blue")
