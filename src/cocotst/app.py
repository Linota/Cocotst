import base64
import random
from os import PathLike
from typing import Literal, Optional, Union

import aiofiles
from aiohttp import ClientSession
from aiohttp.connector import TCPConnector
from creart import it
from graia.broadcast import Broadcast
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from launart import Launart, Service
from loguru import logger
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from uvicorn.config import Config
from cocotst.config import DebugConfig
from cocotst.event.builtin import DebugFlagSetup
from cocotst.event.message import C2CMessage, GroupMessage, MessageEvent
from cocotst.message.element import Ark, Element, Embed, Markdown, MediaElement
from cocotst.network.model import FileServerConfig, Target, WebHookConfig
from cocotst.network.services import QAuth, UvicornService
from cocotst.network.webhook import postevent
from cocotst.utils import get_msg_type
from richuru import install

install()


class Cocotst:
    """Cocotst 实例。"""

    appid: str
    """在开放平台管理端上获得。"""
    clientSecret: str
    """在开放平台管理端上获得。"""
    mgr: Launart
    """Launart 实例。默认自动创建。"""
    broadcast: Broadcast
    """Broadcast 实例."""
    webhook_config: WebHookConfig
    """WebHook 配置。请自行反向代理 WebHook。"""
    file_server_config: FileServerConfig
    """文件服务器配置。"""
    is_sand_box: bool
    """是否使用沙箱模式。"""
    random_msgseq: bool = True
    """是否随机生成 msg_seq。这决定了是否可以重复回复相同的消息。"""
    debug: Optional[DebugConfig] = None
    """调试配置。"""

    def __init__(
        self,
        appid: str,
        clientSecret: str,
        mgr: Launart = it(Launart),
        webhook_config: Optional[WebHookConfig] = None,
        file_server_config: Optional[FileServerConfig] = None,
        is_sand_box: bool = False,
        random_msgseq: bool = True,
        debug: Optional[DebugConfig] = None,
    ):
        """初始化 Cocotst 实例。

        Args:
            appid (str): 在开放平台管理端上获得。
            clientSecret (str): 在开放平台管理端上获得。
            mgr (Launart, optional): Launart 实例。默认自动创建。
            webhook_config (Optional[WebHookConfig], optional): WebHook 配置。请自行反向代理 WebHook。
            file_server_config (Optional[FileServerConfig], optional): 文件服务器配置。
            is_sand_box (bool, optional): 是否使用沙箱模式。
            random_msgseq (bool, optional): 是否随机生成 msg_seq。这决定了是否可以重复回复相同的消息。
            debug (Optional[DebugConfig], optional): 调试配置。
        """
        self.appid = appid
        self.clientSecret = clientSecret
        self.mgr = mgr
        self.broadcast = it(Broadcast)
        self.webhook_config = webhook_config or WebHookConfig()
        self.file_server_config = file_server_config or FileServerConfig()
        self.is_sand_box = is_sand_box
        self.random_msgseq = random_msgseq
        if debug:
            logger.debug("[Cocotst] DebugMode: True")
            logger.debug("[Cocotst] DebugConfig: {}", debug)
            self.broadcast.postEvent(DebugFlagSetup(debug_config=debug))
            self.verify_ssl = debug.api_call.ssl_verify

    async def common_api(self, path: str, method: str, **kwargs):
        connector = TCPConnector(verify_ssl=self.debug.api_call.ssl_verify) if self.verify_ssl else None
        async with ClientSession(connector=connector) as session:
            async with session.request(
                method,
                (
                    f"https://api.sgroup.qq.com{path}"
                    if not self.is_sand_box
                    else f"https://sandbox.api.sgroup.qq.com{path}"
                ),
                headers={"Authorization": f"QQBot {self.mgr.get_component(QAuth).access_token.access_token}"},
                **kwargs,
            ) as resp:
                return await resp.json()

    async def basic_send_group_message(
        self,
        msg_type: Literal[0, 2, 3, 4, 7],
        group_openid: str,
        markdown: Optional[Markdown] = None,  # 待完成
        keyboard: Optional[Embed] = None,  # 待完成
        ark: Optional[Ark] = None,
        message_reference: Optional[object] = None,
        event_id: Optional[str] = None,
        msg_id: Optional[str] = None,
        msg_seq: Optional[int] = None,
        content: str = " ",
        file: Optional[Union[PathLike, bytes, None]] = None,
        file_type: Optional[Literal["image", "video", "voice", 4]] = None,
    ):
        """发送群消息

        Args:
            content: 消息内容
            msg_type: 消息类型 消息类型：0 是文本，2 是 markdown， 3 ark，4 embed，7 media 富媒体
            group_openid: 群组 openid，未填写时且非主动发送时，将会自动获取
            markdown: markdown 内容
            keyboard: 键盘内容
            ark: ark 内容
            message_reference: 引用消息
            event_id: 前置收到的事件 ID，用于发送被动消息，支持事件："INTERACTION_CREATE"、"C2C_MSG_RECEIVE"、"FRIEND_ADD"
            msg_id: 前置收到的用户发送过来的消息 ID，用于发送被动（回复）消息，未填写时且非主动发送时，将会自动获取
            msg_seq: 回复消息的序号，与 msg_id 联合使用，避免相同消息id回复重复发送，不填默认是1。相同的 msg_id + msg_seq 重复发送会失败。
            file: 文件路径或者文件二进制数据
            file_type: 文件类型
        """
        if file or file_type:
            try:
                assert file and file_type
            except AssertionError:
                logger.error("[App.basicSendGroupMessage] file 和 file_type 必须同时存在")
                raise ValueError("file 和 file_type 必须同时存在")
            file_type = ["image", "video", "voice", 4].index(file_type)
            media = await self.post_group_file(
                group_openid,
                file_type + 1,
                file_path=file if isinstance(file, PathLike) else None,
                file_data=file if not isinstance(file, PathLike) else None,
            )
            msg_type = 7
        else:
            media = None
        """
        if markdown:
            msg_type = 2
        if ark:
            msg_type = 3
        if embed:
            msg_type = 4
        """

        return await self.common_api(
            f"/v2/groups/{group_openid}/messages",
            "POST",
            json={
                "content": content,
                "msg_type": msg_type,
                "markdown": markdown,
                "keyboard": keyboard,
                "media": media,
                "ark": ark,
                "message_reference": message_reference,
                "event_id": event_id,
                "msg_id": msg_id,
                "msg_seq": random.randint(1, 100) if self.random_msgseq else msg_seq,
                "media": media,
            },
        )

    async def send_group_message(
        self,
        target: Target,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ):
        """发送群消息

        Args:
            target (Target): 目标,非主动消息时，需传入前置消息 ID 或者事件 ID.
            content (Content): 内容,仅在文本消息或者文图消息时有效，仅发送图片时为空格
            element (Element): 消息元素
            proactive (bool, optional): 是否主动发送. 将会占用主动发送次数。

        """
        try:
            assert (target.target_id or target.event_id) and not proactive
        except AssertionError:
            logger.error("[App.sendGroupMsg] 发送被动消息时必须提供 target.target_id 或 target.event_id ")
            raise ValueError("发送被动消息时必须提供 target.target_id 或 target.event_id ")

        return await self.basic_send_group_message(
            msg_type=get_msg_type(content, element),
            group_openid=target.target_unit,
            content=content,
            file=(await element.as_data_bytes() if isinstance(element, MediaElement) else None),
            file_type=element.type if isinstance(element, MediaElement) else None,
            event_id=target.event_id,
            msg_id=target.target_id,
            markdown=element if isinstance(element, Markdown) else None,
            ark=element if isinstance(element, Ark) else None,
            keyboard=element if isinstance(element, Embed) else None,
        )

    async def basic_send_c2c_message(
        self,
        msg_type: Literal[0, 2, 3, 4, 7],
        openid: str,
        markdown: Optional[Markdown] = None,
        keyboard: Optional[Embed] = None,
        ark: Optional[Ark] = None,
        message_reference: Optional[object] = None,
        event_id: Optional[str] = None,
        msg_id: Optional[str] = None,
        msg_seq: Optional[int] = None,
        content: str = " ",
        file: Optional[Union[PathLike, bytes, None]] = None,
        file_type: Optional[Literal["image", "video", "voice", 4]] = None,
    ):
        """发送私聊消息

        Args:


            content: 消息内容
            msg_type: 消息类型 消息类型：0 是文本，2 是 markdown， 3 ark，4 embed，7 media 富媒体
            openid: 用户 openid
            markdown: markdown 内容
            keyboard: 键盘内容
            ark: ark 内容
            message_reference: 引用消息
            event_id: 前置收到的事件 ID，用于发送被动消息，支持事件："INTERACTION_CREATE"、"C2C_MSG_RECEIVE"、"FRIEND_ADD"
            msg_id: 前置收到的用户发送过来的消息 ID，用于发送被动（回复）消息，未填写时且非主动发送时，将会自动获取
            msg_seq: 回复消息的序号，与 msg_id 联合使用，避免相同消息id回复重复发送，不填默认是1。相同的 msg_id + msg_seq 重复发送会失败.
            file: 文件路径或者文件二进制数据
            file_type: 文件类型
        """
        if file or file_type:
            try:
                assert file and file_type
            except AssertionError:
                logger.error("[App.basicSendC2CMessage] file 和 file_type 必须同时存在")
                raise ValueError("file 和 file_type 必须同时存在")
            file_type = ["image", "video", "voice", 4].index(file_type)
            media = await self.post_c2c_file(
                openid,
                file_type + 1,
                file_path=file if isinstance(file, PathLike) else None,
                file_data=file if not isinstance(file, PathLike) else None,
            )

        else:
            media = None
        return await self.common_api(
            f"/v2/users/{openid}/messages",
            "POST",
            json={
                "content": content,
                "msg_type": msg_type,
                "markdown": markdown,
                "keyboard": keyboard,
                "media": media,
                "ark": ark,
                "message_reference": message_reference,
                "event_id": event_id,
                "msg_id": msg_id,
                "msg_seq": random.randint(1, 100) if self.random_msgseq else msg_seq,
            },
        )

    async def send_c2c_message(
        self,
        target: Target,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ):
        """发送私聊消息

        Args:

            target (Target): 目标,非主动消息时，需传入前置消息 ID 或者事件 ID.
            content (Content): 内容,仅在文本消息或者文图消息时有效，仅发送图片时为空格
            element (Element): 消息元素
            proactive (bool, optional): 是否主动发送. 将会占用主动发送次数。
        """
        try:
            assert (target.target_id or target.event_id) and not proactive
        except AssertionError:
            logger.error("[App.sendC2CMsg] 发送被动消息时必须提供 target.target_id 或 target.event_id ")
            raise ValueError("发送被动消息时必须提供 target.target_id 或 target.event_id ")
        return await self.basic_send_c2c_message(
            msg_type=get_msg_type(content, element),
            openid=target.target_unit,
            content=content,
            file=(await element.as_data_bytes() if isinstance(element, MediaElement) else None),
            file_type=element.type if isinstance(element, MediaElement) else None,
            event_id=target.event_id,
            msg_id=target.target_id,
            markdown=element if isinstance(element, Markdown) else None,
            ark=element if isinstance(element, Ark) else None,
            keyboard=element if isinstance(element, Embed) else None,
        )

    async def send_message(
        self,
        target: MessageEvent,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ):
        """发送消息

        Args:

                target (Target): 目标,非主动消息时，需传入前置事件
                content (Content): 内容,仅在文本消息或者文图消息时有效，仅发送图片时为空格
                element (Element): 消息元素
                proactive (bool, optional): 是否主动发送. 将会占用主动发送次数。
        """
        if isinstance(target, C2CMessage):
            return await self.send_c2c_message(target.target, content, element, proactive)
        if isinstance(target, GroupMessage):
            return await self.send_group_message(target.target, content, element, proactive)

    async def post_group_file(
        self,
        group_openid: str,
        file_type: Literal[1, 2, 3, 4],
        url: Optional[str] = "",
        srv_send_msg: bool = False,
        file_data: Optional[object] = None,
        file_path: Optional[PathLike] = None,
    ) -> str:
        """上传群文件，上传成功后返回文件 ID，用于发送图片等操作"""
        try:
            assert url or file_data or file_path
        except AssertionError:
            logger.error("[App.postGroupFile] url, file_data, file_path 三者必须有一个")
            raise ValueError("url, file_data, file_path 三者必须有一个")
        if file_path:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()
        file_data = base64.b64encode(file_data).decode()
        return await self.common_api(
            f"/v2/groups/{group_openid}/files",
            "POST",
            json={
                "file_type": file_type,
                "url": url,
                "srv_send_msg": srv_send_msg,
                "file_data": file_data,
            },
        )

    async def post_c2c_file(
        self,
        openid: str,
        file_type: Literal[1, 2, 3, 4],
        url: Optional[str] = "",
        srv_send_msg: bool = False,
        file_data: Optional[object] = None,
        file_path: Optional[PathLike] = None,
    ) -> str:
        """上传私聊文件，上传成功后返回文件 ID，用于发送图片等操作"""
        try:
            assert url or file_data or file_path
        except AssertionError:
            logger.error("[App.postC2CFile] url, file_data, file_path 三者必须有一个")
            raise ValueError("url, file_data, file_path 三者必须有一个")
        if file_path:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()
        file_data = base64.b64encode(file_data).decode()
        return await self.common_api(
            f"/v2/users/{openid}/files",
            "POST",
            json={
                "file_type": file_type,
                "url": url,
                "srv_send_msg": srv_send_msg,
                "file_data": file_data,
            },
        )

    @classmethod
    def current(cls) -> "Cocotst":
        """获取当前 Cocotst 实例。"""
        return it(Launart).get_component(App).app

    def launch_blocking(self):
        asgiapp = Starlette(
            routes=[
                Route(self.webhook_config.postevent, postevent, methods=["POST"]),
            ]
        )
        self.mgr.add_component(QAuth(self.appid, self.clientSecret))
        (
            asgiapp.mount(
                self.file_server_config.remote_url,
                app=StaticFiles(directory=self.file_server_config.localpath),
            )
            if self.file_server_config.localpath
            else None
        )
        self.mgr.add_component(
            UvicornService(
                config=Config(
                    app=asgiapp,
                    host=self.webhook_config.host,
                    port=self.webhook_config.port,
                )
            )
        )
        self.mgr.add_component(App(self))
        self.mgr.launch_blocking()


class CocotstDispatcher(BaseDispatcher):

    @staticmethod
    async def catch(interface: DispatcherInterface):
        if interface.annotation == Cocotst:
            mgr = it(Launart)
            return mgr.get_component(App).app


class ApplicationReady:
    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface):
            pass


class App(Service):
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
            broadcast.postEvent(ApplicationReady())

        async with self.stage("blocking"):
            pass

        async with self.stage("cleanup"):
            pass
