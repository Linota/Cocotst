import asyncio
import contextlib

import requests
from aiohttp import ClientSession
from launart import Launart, Service
from loguru import logger
from uvicorn._types import ASGIApplication
from uvicorn.config import Config
from uvicorn.server import Server

from cocotst.network.model import AccessToken


def auth(appid: str, clientSecret: str):
    """
    :param appid: 在开放平台管理端上获得。
    :param clientSecret: 在开放平台管理端上获得。
    :return: AccessToken 实例。
    获取 AccessToken。
    """
    try:
        return AccessToken.model_validate(
            requests.post(
                "https://bots.qq.com/app/getAppAccessToken",
                json={"appId": appid, "clientSecret": clientSecret},
            ).json()
        )
    except Exception as e:
        raise KeyError(f"获取 AccessToken 失败: {e}")


class QAuth(Service):
    """循环鉴权服务。"""

    id = "QAuth"
    appid: str
    """在开放平台管理端上获得。"""
    clientSecret: str
    """在开放平台管理端上获得。"""

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
        """
        :param mgr: Launart 实例。
        :param appid: 在开放平台管理端上获得。
        :param clientSecret: 在开放平台管理端上获得。
        :return: None
        异步鉴权。
        """
        while True:
            await asyncio.sleep(int(self.access_token.expires_in))
            logger.info("[QApi] Refreshing access token!")
            async with ClientSession() as session:
                async with session.post(
                    "https://bots.qq.com/app/getAppAccessToken",
                    json={"appId": appid, "clientSecret": clientSecret},
                ) as resp:
                    self.access_token = AccessToken.model_validate(await resp.json())
            logger.info("[QApi] Access token refreshed")

    async def launch(self, mgr: Launart):

        async with self.stage("preparing"):
            logger.info("[QApi] Start fetching access token!")
            self.access_token = auth(self.appid, self.clientSecret)
        logger.info(f"[QApi] Access token Fetched")

        async with self.stage("blocking"):

            query_tsk = asyncio.create_task(self.auth_async(mgr, self.appid, self.clientSecret))
            await mgr.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            query_tsk.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await query_tsk
            logger.info("[QApi] Service stopped")


class UvicornService(Service):
    """Uvicorn 服务。"""

    id = "UvicornService"
    config: Config
    """Uvicorn 配置。"""

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
            logger.info("[UvicornService] Start running server!")

        async with self.stage("blocking"):
            server_task = asyncio.create_task(server.serve())
            await mgr.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            server_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await server_task
            logger.info("[UvicornService] Service stopped")
