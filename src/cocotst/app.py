import random
from typing import Optional, Union, overload

from creart import it
from graia.broadcast import Broadcast
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from launart import Launart, Service
from loguru import logger
from richuru import install
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from uvicorn.config import Config

from cocotst.config.debug import DebugConfig
from cocotst.event.builtin import DebugFlagSetup
from cocotst.event.message import C2CMessage, GroupMessage, MessageEvent, MessageSent
from cocotst.message.element import Element, MediaElement
from cocotst.config.webserver import FileServerConfig, WebHookConfig
from cocotst.network.model.target import Target
from cocotst.network.model.http_api import OpenAPIErrorCallback
from cocotst.network.services import AiohttpClientSessionService, QAuth, UvicornService
from cocotst.network.webhook import postevent
from cocotst.utils import get_msg_type
from cocotst.network.qqapi import QQAPI, MessageRecallError, MessageTarget
from cocotst.utils.debug import print_debug_tree

install()


class Cocotst:
    """
    Cocotst 实例，集成了 QQ 机器人的核心功能。
    该类作为主要接口，统筹管理消息处理、事件分发和网络请求。
    """

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
        """
        初始化 Cocotst 实例。

        Args:
            appid: QQ开放平台的应用ID
            clientSecret: QQ开放平台的应用密钥
            mgr: Launart 实例，用于管理服务生命周期
            webhook_config: WebHook 配置
            file_server_config: 文件服务器配置
            is_sand_box: 是否使用沙箱环境
            random_msgseq: 是否随机生成消息序号
            debug: 调试配置
        """
        self.appid = appid
        self.clientSecret = clientSecret
        self.mgr = mgr
        self.broadcast = it(Broadcast)
        self.webhook_config = webhook_config or WebHookConfig()
        self.file_server_config = file_server_config or FileServerConfig()
        self.is_sand_box = is_sand_box
        self.random_msgseq = random_msgseq
        self.debug = debug
        self._api: Optional[QQAPI] = None  # 初始化时先设为 None

        # 设置调试模式
        if debug:
            logger.warning("[Cocotst] 设置调试模式", style="bold yellow")
            logger.warning(f"[Cocotst] 调试配置: \n{print_debug_tree(debug)}", style="bold yellow")
            self.broadcast.postEvent(DebugFlagSetup(debug_config=debug))

    @property
    def api(self) -> QQAPI:
        """
        获取 QQAPI 实例。如果尚未初始化，则创建新实例。
        这种延迟初始化的方式确保在获取 access_token 后才创建 API 实例。
        """
        if self._api is None:
            self._api = QQAPI(
                app_id=self.appid,
                client_secret=self.clientSecret,
                is_sandbox=self.is_sand_box,
                debug_config=self.debug,
            )
        return self._api

    async def send_group_message(
        self,
        target: Target,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ) -> Union[MessageSent, OpenAPIErrorCallback]:
        """
        发送群消息的统一接口。

        Args:
            target: 消息目标信息
            content: 消息内容
            element: 消息元素（如图片、视频等）
            proactive: 是否主动发送

        Returns:
            消息发送结果
        """
        # 验证消息发送条件
        if not proactive and not (target.target_id or target.event_id):
            logger.error("[Cocotst.sendGroupMsg] 发送被动消息时必须提供 target.target_id 或 target.event_id")
            raise ValueError("发送被动消息时必须提供 target.target_id 或 target.event_id")

        # 准备消息数据
        message_data = await self.api.prepare_message_data(
            content=content,
            element=element,
            msg_type=get_msg_type(content, element),
            event_id=target.event_id,
            msg_id=target.target_id,
            msg_seq=random.randint(1, 100) if self.random_msgseq else None,
        )

        # 发送消息
        try:
            response = await self.api.send_message(
                target_type="group",
                target_id=target.target_unit,
                message_data=message_data,
                media_element=element if isinstance(element, MediaElement) else None,
            )
            return MessageSent(**response)
        except Exception as e:
            logger.error(f"[Cocotst.sendGroupMsg] 发送消息失败: {e}")
            raise

    async def send_c2c_message(
        self,
        target: Target,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ) -> Union[MessageSent, OpenAPIErrorCallback]:
        """
        发送私聊消息的统一接口。

        Args:
            target: 消息目标信息
            content: 消息内容
            element: 消息元素（如图片、视频等）
            proactive: 是否主动发送

        Returns:
            消息发送结果
        """
        if not proactive and not (target.target_id or target.event_id):
            logger.error("[Cocotst.sendC2CMsg] 发送被动消息时必须提供 target.target_id 或 target.event_id")
            raise ValueError("发送被动消息时必须提供 target.target_id 或 target.event_id")

        message_data = await self.api.prepare_message_data(
            content=content,
            element=element,
            msg_type=get_msg_type(content, element),
            event_id=target.event_id,
            msg_id=target.target_id,
            msg_seq=random.randint(1, 100) if self.random_msgseq else None,
        )

        try:
            response = await self.api.send_message(
                target_type="c2c",
                target_id=target.target_unit,
                message_data=message_data,
                media_element=element if isinstance(element, MediaElement) else None,
            )
            return MessageSent(**response)
        except Exception as e:
            logger.error(f"[Cocotst.sendC2CMsg] 发送消息失败: {e}")
            raise

    async def send_message(
        self,
        target: MessageEvent,
        content: str = " ",
        element: Optional[Element] = None,
        proactive: bool = False,
    ) -> Union[MessageSent, OpenAPIErrorCallback]:
        """
        统一的消息发送接口，根据消息类型自动选择发送方式。

        Args:
            target: 消息事件
            content: 消息内容
            element: 消息元素
            proactive: 是否主动发送

        Returns:
            消息发送结果
        """
        if isinstance(target, C2CMessage):
            return await self.send_c2c_message(target.target, content, element, proactive)
        if isinstance(target, GroupMessage):
            return await self.send_group_message(target.target, content, element, proactive)
        raise ValueError(f"Unsupported message type: {type(target)}")

    async def _get_target_id(self, target: Union[str, Target, MessageEvent]) -> str:
        """
        从不同类型的目标参数中提取目标ID。这个辅助方法用于统一处理不同形式的目标参数。

        参数:
            target: 可以是目标ID字符串、Target对象或MessageEvent对象

        返回:
            str: 提取出的目标ID
        """
        if isinstance(target, str):
            return target
        elif isinstance(target, MessageEvent):
            return target.target.target_unit
        elif isinstance(target, Target):
            return target.target_unit
        else:
            raise ValueError(f"不支持的目标类型: {type(target)}")

    @overload
    async def recall_group_message(self, group_openid: str, message_id: str) -> bool: ...

    @overload
    async def recall_group_message(self, group_openid: Target, message_id: str) -> bool: ...

    @overload
    async def recall_group_message(self, group_openid: GroupMessage, message_id: str) -> bool: ...

    async def recall_group_message(
        self, group_openid: Union[str, Target, GroupMessage], message_id: str
    ) -> bool:
        """
        撤回群聊消息。支持多种方式指定目标群聊。

        这个方法支持三种方式来指定目标群聊：
        1. 直接使用群的openid字符串
        2. 使用Target对象
        3. 使用GroupMessage事件对象

        群聊消息撤回的限制：
        1. 只能撤回2分钟内发送的消息
        2. 机器人只能撤回自己发送的消息
        3. 管理员和群主可以撤回普通成员的消息

        参数:
            group_openid: 群聊标识，可以是openid字符串、Target对象或GroupMessage对象
            message_id: 需要撤回的消息ID

        返回:
            bool: 撤回操作是否成功

        示例:
            await bot.recall_group_message("group123", "msg456")
            await bot.recall_group_message(target_obj, "msg456")
            await bot.recall_group_message(group_message_event, "msg456")
        """
        try:
            target_id = await self._get_target_id(group_openid)
            return await self.api.recall_message(
                target_type=MessageTarget.GROUP, target_id=target_id, message_id=message_id
            )
        except MessageRecallError as e:
            logger.error(f"[Cocotst.recallGroupMessage] 群聊消息撤回失败: {e}")
            return False
        except ValueError as e:
            logger.error(f"[Cocotst.recallGroupMessage] 参数错误: {e}")
            return False

    @overload
    async def recall_c2c_message(self, openid: str, message_id: str) -> bool: ...

    @overload
    async def recall_c2c_message(self, openid: Target, message_id: str) -> bool: ...

    @overload
    async def recall_c2c_message(self, openid: C2CMessage, message_id: str) -> bool: ...

    async def recall_c2c_message(self, openid: Union[str, Target, C2CMessage], message_id: str) -> bool:
        """
        撤回私聊消息。支持多种方式指定目标用户。

        这个方法支持三种方式来指定目标用户：
        1. 直接使用用户的openid字符串
        2. 使用Target对象
        3. 使用C2CMessage事件对象

        私聊消息撤回的限制：
        1. 只能撤回2分钟内发送的消息
        2. 机器人只能撤回自己发送的消息

        参数:
            openid: 用户标识，可以是openid字符串、Target对象或C2CMessage对象
            message_id: 需要撤回的消息ID

        返回:
            bool: 撤回操作是否成功

        示例:
            await bot.recall_c2c_message("user123", "msg456")
            await bot.recall_c2c_message(target_obj, "msg456")
            await bot.recall_c2c_message(c2c_message_event, "msg456")
        """
        try:
            target_id = await self._get_target_id(openid)
            return await self.api.recall_message(
                target_type=MessageTarget.C2C, target_id=target_id, message_id=message_id
            )
        except MessageRecallError as e:
            logger.error(f"[Cocotst.recallC2CMessage] 私聊消息撤回失败: {e}")
            return False
        except ValueError as e:
            logger.error(f"[Cocotst.recallC2CMessage] 参数错误: {e}")
            return False

    @overload
    async def recall_channel_message(
        self, channel_id: str, message_id: str, hide_tip: bool = False
    ) -> bool: ...

    @overload
    async def recall_channel_message(
        self, channel_id: Target, message_id: str, hide_tip: bool = False
    ) -> bool: ...

    async def recall_channel_message(
        self, channel_id: Union[str, Target], message_id: str, hide_tip: bool = False
    ) -> bool:
        """
        撤回子频道消息。支持使用ID字符串或Target对象指定目标子频道。

        这个方法支持两种方式来指定目标子频道：
        1. 直接使用子频道ID字符串
        2. 使用Target对象

        子频道消息撤回的特点：
        1. 管理员可以撤回普通成员的消息
        2. 频道主可以撤回所有人的消息
        3. 普通成员只能撤回自己的消息

        参数:
            channel_id: 子频道标识，可以是ID字符串或Target对象
            message_id: 需要撤回的消息ID
            hide_tip: 是否隐藏撤回提示

        返回:
            bool: 撤回操作是否成功

        注意:
            此功能仅对私域机器人可用
        """
        try:
            target_id = channel_id if isinstance(channel_id, str) else getattr(channel_id, "channel_id", None)
            if target_id is None:
                raise ValueError("无法从提供的参数中获取channel_id")

            return await self.api.recall_message(
                target_type=MessageTarget.CHANNEL,
                target_id=target_id,
                message_id=message_id,
                hide_tip=hide_tip,
            )
        except MessageRecallError as e:
            logger.error(f"[Cocotst.recallChannelMessage] 子频道消息撤回失败: {e}")
            return False
        except ValueError as e:
            logger.error(f"[Cocotst.recallChannelMessage] 参数错误: {e}")
            return False

    @overload
    async def recall_dms_message(self, guild_id: str, message_id: str, hide_tip: bool = False) -> bool: ...

    @overload
    async def recall_dms_message(self, guild_id: Target, message_id: str, hide_tip: bool = False) -> bool: ...

    async def recall_dms_message(
        self, guild_id: Union[str, Target], message_id: str, hide_tip: bool = False
    ) -> bool:
        """
        撤回频道私信消息。支持使用ID字符串或Target对象指定目标频道。

        这个方法支持两种方式来指定目标频道：
        1. 直接使用guild_id字符串
        2. 使用Target对象

        频道私信消息撤回的特点：
        1. 机器人只能撤回自己发送的私信消息
        2. 可以选择是否显示撤回提示
        3. 需要私域机器人权限

        参数:
            guild_id: 频道标识，可以是ID字符串或Target对象
            message_id: 需要撤回的消息ID
            hide_tip: 是否隐藏撤回提示

        返回:
            bool: 撤回操作是否成功

        注意:
            此功能仅对私域机器人可用
        """
        try:
            target_id = guild_id if isinstance(guild_id, str) else getattr(guild_id, "guild_id", None)
            if target_id is None:
                raise ValueError("无法从提供的参数中获取guild_id")

            return await self.api.recall_message(
                target_type=MessageTarget.DMS, target_id=target_id, message_id=message_id, hide_tip=hide_tip
            )
        except MessageRecallError as e:
            logger.error(f"[Cocotst.recallDMSMessage] 频道私信消息撤回失败: {e}")
            return False
        except ValueError as e:
            logger.error(f"[Cocotst.recallDMSMessage] 参数错误: {e}")
            return False

    @classmethod
    def current(cls) -> "Cocotst":
        """获取当前 Cocotst 实例。"""
        return it(Launart).get_component(App).app

    def launch_blocking(self):
        """
        启动 Cocotst 实例，设置必要的服务和组件。
        """
        # 创建 ASGI 应用
        asgiapp = Starlette(
            routes=[
                Route(self.webhook_config.postevent, postevent, methods=["POST"]),
            ]
        )
        # 添加 Aiohttp 服务组件
        self.mgr.add_component(
            AiohttpClientSessionService()
        )
        # 添加认证组件
        self.mgr.add_component(QAuth(self.appid, self.clientSecret))

        # 配置文件服务器
        if self.file_server_config.localpath:
            asgiapp.mount(
                self.file_server_config.remote_url,
                app=StaticFiles(directory=self.file_server_config.localpath),
            )

        # 添加 Uvicorn 服务
        self.mgr.add_component(
            UvicornService(
                config=Config(
                    app=asgiapp,
                    host=self.webhook_config.host,
                    port=self.webhook_config.port,
                )
            )
        )

        # 添加应用组件并启动
        self.mgr.add_component(App(self))
        self.mgr.launch_blocking()


# 以下是辅助类的实现


class CocotstDispatcher(BaseDispatcher):
    """Cocotst 的调度器实现"""

    @staticmethod
    async def catch(interface: DispatcherInterface):
        if interface.annotation == Cocotst:
            mgr = it(Launart)
            return mgr.get_component(App).app


class ApplicationReady:
    """应用就绪事件类"""

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface):
            pass


class App(Service):
    """Cocotst 应用服务类"""

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
            logger.info("[APP] Inject Dispatchers", style="bold blue")
            broadcast = it(Broadcast)
            broadcast.finale_dispatchers.append(CocotstDispatcher())
            logger.info("[APP] Injected Dispatchers", style="bold green")
            broadcast.postEvent(ApplicationReady())
        async with self.stage("blocking"):
            pass
        async with self.stage("cleanup"):
            pass
