from typing import Literal, Optional, Union, TypedDict
from os import PathLike
import base64
import aiofiles
from aiohttp import ClientSession
from loguru import logger

from cocotst.config.debug import DebugConfig
from cocotst.message.element import Ark, Element, Embed, Markdown, MediaElement
from cocotst.network.model.http_api import OpenAPIErrorCallback
from launart import Launart

from enum import Enum

from cocotst.network.services import QAuth


class MessageTarget(Enum):
    """消息撤回的目标类型枚举。

    定义了不同类型消息的API路径模板。使用 {target_id} 和 {message_id} 作为占位符，
    这样可以在运行时动态填充实际的ID值。
    """

    GROUP = "/v2/groups/{target_id}/messages/{message_id}"  # 群聊消息
    C2C = "/v2/users/{target_id}/messages/{message_id}"  # 单聊消息
    CHANNEL = "/channels/{target_id}/messages/{message_id}"  # 子频道消息
    DMS = "/dms/{target_id}/messages/{message_id}"  # 频道私信


class FileUploadResponse(TypedDict):
    """文件上传响应的类型定义"""

    file_uuid: str
    file_info: str
    ttl: int


class MessageData(TypedDict):
    """消息数据的类型定义"""

    content: str
    msg_type: Literal[0, 2, 3, 4, 7]
    markdown: Optional[Markdown]
    keyboard: Optional[Embed]
    media: Optional[str]
    ark: Optional[Ark]
    message_reference: Optional[object]
    event_id: Optional[str]
    msg_id: Optional[str]
    msg_seq: Optional[int]


class QQAPIError(Exception):
    """QQ API 相关错误的基类"""

    pass


class FileUploadError(QQAPIError):
    """文件上传错误"""

    pass


class MessageSendError(QQAPIError):
    """消息发送错误"""

    pass


class MessageRecallError(QQAPIError):
    """消息撤回相关错误"""

    pass


class QQAPI:
    """
    封装QQ机器人API调用的类。处理与QQ开放平台的所有网络通信。
    """

    def __init__(
        self,
        app_id: str,
        client_secret: str,
        is_sandbox: bool = False,
        debug_config: Optional[DebugConfig] = None,
    ):
        """
        初始化QQ API客户端。

        参数:
            app_id: 应用的ID
            client_secret: 应用的密钥
            access_token: 访问令牌
            is_sandbox: 是否使用沙箱环境
            debug_config: 调试配置
        """
        self.app_id = app_id
        self.client_secret = client_secret
        self.is_sandbox = is_sandbox
        self.debug_config = debug_config

        # 设置API基础URL
        self.api_host = "sandbox.api.sgroup.qq.com" if is_sandbox else "api.sgroup.qq.com"
        self.api_base = f"https://{self.api_host}"

    async def common_api(self, path: str, method: str, **kwargs) -> Union[dict, OpenAPIErrorCallback]:
        """
        通用API请求方法。处理所有与QQ开放平台的HTTP通信。

        参数:
            path: API路径
            method: HTTP方法（GET、POST、DELETE等）
            **kwargs: 传递给 aiohttp 的额外参数

        返回:
            API响应数据或错误回调对象
        """
        # 构建完整的URL
        url = f"{self.api_base}{path}"

       

        try:
            async with ClientSession() as session:
                # 设置请求头
                headers = {"Authorization": f"QQBot {Launart.current().get_component(QAuth).access_token}", "Content-Type": "application/json"}

                # 发送请求
                async with session.request(method, url, headers=headers, **kwargs) as resp:
                    # 获取响应数据
                    rt = await resp.json()

                    # 检查是否有错误
                    if "code" in rt:
                        cb = OpenAPIErrorCallback(**rt)
                        logger.error("[QQAPI.commonApi] OpenAPI错误: {}", cb, style="bold red")
                        return cb
                    return rt

        except Exception as e:
            # 详细记录错误信息
            logger.error("[QQAPI.commonApi] 请求失败: {}\nURL: {}\n方法: {}", str(e), url, method)
            raise

    async def upload_file(
        self,
        target_type: Literal["group", "c2c"],
        target_id: str,
        file_type: Literal[1, 2, 3, 4],
        url: Optional[str] = None,
        file_data: Optional[bytes] = None,
        file_path: Optional[PathLike] = None,
        srv_send_msg: bool = False,
    ) -> str:
        """
        统一的文件上传方法

        Args:
            target_type: 目标类型 (group/c2c)
            target_id: 目标 ID
            file_type: 文件类型 (1:图片 2:视频 3:语音 4:文件)
            url: 文件 URL
            file_data: 文件二进制数据
            file_path: 文件路径
            srv_send_msg: 是否由服务器发送消息

        Returns:
            文件 ID

        Raises:
            FileUploadError: 当文件上传失败时
        """
        if not any([url, file_data, file_path]):
            raise FileUploadError("必须提供 url、file_data 或 file_path 中的一个")

        # 如果提供了文件路径，读取文件内容
        if file_path:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()

        # 准备请求数据
        data = {
            "file_type": file_type,
            "srv_send_msg": srv_send_msg,
        }

        if url:
            data["url"] = url
        elif file_data:
            data["file_data"] = base64.b64encode(file_data).decode()

        # 构建 API 路径
        path = f"/v2/groups/{target_id}/files" if target_type == "group" else f"/v2/users/{target_id}/files"

        response = await self.common_api(path, "POST", json=data)

        if isinstance(response, OpenAPIErrorCallback):
            raise FileUploadError(f"文件上传失败: {response}")

        return response

    def _log_message_sent(
        self,
        message_type: str,
        target_id: str,
        message_id: str,
        content: Optional[str] = None,
        media_element: Optional[MediaElement] = None,
    ) -> None:
        """
        记录消息发送成功的日志，使用纯树形结构展示所有信息。
        所有信息都使用树形层次展示，不使用分隔符。
        """
        # 收集所有日志节点
        log_lines = ["[消息发送成功]"]

        # 添加基础信息作为第一层节点
        log_lines.extend(
            ["├── 类型: " + message_type, "├── 消息ID: " + message_id, "├── 目标ID: " + target_id]
        )

        # 添加可选的消息内容
        if content and content.strip() != " ":
            content_preview = content[:50] + "..." if len(content) > 50 else content
            if media_element:  # 如果还有媒体信息要添加，使用├──
                log_lines.append("├── 内容: " + content_preview)
            else:  # 如果是最后一项，使用└──
                log_lines.append("└── 内容: " + content_preview)

        # 添加媒体信息（如果有）
        if media_element:
            media_types = ["image", "video", "voice", "file"]
            try:
                media_type_num = media_types.index(media_element.type) + 1
                log_lines.append(f"└── 媒体类型: {media_element.type}({media_type_num})")
            except ValueError:
                log_lines.append(f"└── 媒体类型: {media_element.type}")

        # 使用换行符连接所有行
        full_log = "\n".join(log_lines)

        # 使用绿色样式记录成功日志
        logger.info(full_log, style="bold green")

    def _log_message_recall(
        self, message_type: str, target_id: str, message_id: str, hide_tip: bool = False, success: bool = True
    ) -> None:
        """
        记录消息撤回操作的日志，使用纯树形结构展示所有信息。
        所有信息都使用树形层次展示，不使用分隔符。
        """
        # 收集所有日志节点
        log_lines = [f"[消息撤回{'成功' if success else '失败'}]"]

        # 添加基础信息作为第一层节点
        log_lines.extend(
            ["├── 类型: " + message_type, "├── 消息ID: " + message_id, "├── 目标ID: " + target_id]
        )

        # 添加隐藏提示信息（如果适用）
        if message_type in ["channel", "dms"] and hide_tip:
            log_lines.append("└── 隐藏提示: 是")
        else:
            # 如果没有隐藏提示信息，将最后一个基础信息的前缀改为└──
            log_lines[-1] = log_lines[-1].replace("├──", "└──")

        # 使用换行符连接所有行
        full_log = "\n".join(log_lines)

        # 根据操作结果选择日志样式
        log_style = "bold green" if success else "bold red"

        # 记录带样式的日志信息
        logger.info(full_log, style=log_style)

    def _get_media_type(self, media_element: MediaElement) -> int:
        """
        将媒体元素类型转换为API所需的数字格式。

        QQ机器人API使用1-4的数字来表示不同的媒体类型：
        1: 图片(image)
        2: 视频(video)
        3: 语音(voice)
        4: 文件(file)

        参数:
            media_element: 包含type属性的媒体元素

        返回:
            int: 对应的媒体类型数字(1-4)

        异常:
            ValueError: 当传入未知的媒体类型时抛出
        """
        media_types = ["image", "video", "voice", "file"]
        try:
            return media_types.index(media_element.type) + 1
        except ValueError:
            raise ValueError(f"不支持的媒体类型: {media_element.type}")

    async def prepare_message_data(
        self,
        content: str = " ",
        element: Optional[Element] = None,
        msg_type: Optional[Literal[0, 2, 3, 4, 7]] = None,
        event_id: Optional[str] = None,
        msg_id: Optional[str] = None,
        msg_seq: Optional[int] = None,
    ) -> MessageData:
        """
        准备发送消息所需的数据。会根据元素类型自动设置正确的消息类型和媒体信息。

        参数:
            content: 消息内容
            element: 消息元素(可以是MediaElement、Markdown、Embed、Ark等)
            msg_type: 消息类型(如果不指定，会根据element自动判断)
            event_id: 事件ID
            msg_id: 消息ID
            msg_seq: 消息序号
        """
        # 基础消息数据
        message_data: MessageData = {
            "content": content,
            "msg_type": msg_type or 0,  # 默认为文本消息
            "markdown": element if isinstance(element, Markdown) else None,
            "keyboard": element if isinstance(element, Embed) else None,
            "ark": element if isinstance(element, Ark) else None,
            "media": None,
            "message_reference": None,
            "event_id": event_id,
            "msg_id": msg_id,
            "msg_seq": msg_seq,
        }
        return message_data

    async def send_message(
        self,
        target_type: Literal["group", "c2c", "channel", "dms"],
        target_id: str,
        message_data: dict,
        media_element: Optional[MediaElement] = None,
    ) -> dict:
        """
        发送消息的统一方法。

        现在这个方法不再需要手动处理媒体类型的转换，因为message_data中
        已经包含了正确的媒体类型信息。它只需要负责发送消息和记录日志。
        """
        path_map = {
            "group": f"/v2/groups/{target_id}/messages",
            "c2c": f"/v2/users/{target_id}/messages",
            "channel": f"/channels/{target_id}/messages",
            "dms": f"/dms/{target_id}/messages",
        }

        path = path_map[target_type]
        # 处理媒体元素
        if media_element:
            file_id = await self.upload_file(
                target_type,
                target_id,
                file_type=self._get_media_type(media_element),
                file_data=await media_element.as_data_bytes(),
            )
            message_data["media"] = file_id
            message_data["msg_type"] = 7  # 富媒体消息类型

        # 发送请求
        response = await self.common_api(path, "POST", json=message_data)

        # 处理响应
        if isinstance(response, OpenAPIErrorCallback):
            logger.error(
                f"[消息发送失败] 类型: {target_type} | 目标: {target_id} | 错误: {response}", style="bold red"
            )
            return response

        # 记录成功发送的日志
        self._log_message_sent(
            message_type=target_type,
            target_id=target_id,
            message_id=response.get("id", "unknown"),
            content=message_data.get("content"),
            media_element=media_element,
        )

        return response

    async def recall_message(
        self, target_type: MessageTarget, target_id: str, message_id: str, hide_tip: bool = False
    ) -> bool:
        """
        统一的消息撤回方法。支持所有类型的消息撤回操作。

        这个方法通过API实现消息的撤回功能，并提供详细的日志记录。日志会包含操作
        的所有关键信息，包括目标类型、消息ID、操作结果等，便于追踪和调试。

        参数:
            target_type: 消息目标类型（MessageTarget枚举值）
            target_id: 目标ID
            message_id: 要撤回的消息ID
            hide_tip: 是否隐藏撤回提示（仅用于子频道和私信）

        返回:
            bool: 撤回是否成功
        """
        try:
            # 首先记录开始执行撤回操作的日志
            logger.debug(
                f"[QQAPI.recallMessage] 开始撤回消息 | 类型: {target_type.name} | "
                f"目标: {target_id} | 消息ID: {message_id}",
                style="bold blue",
            )

            # 构造API路径
            path = target_type.value.format(target_id=target_id, message_id=message_id)

            # 对于子频道和私信，添加hide_tip参数
            if target_type in [MessageTarget.CHANNEL, MessageTarget.DMS] and hide_tip:
                path += "?hidetip=true"

            # 记录实际请求的API路径
            logger.debug(f"[QQAPI.recallMessage] 请求路径: {path}", style="blue")

            # 发送撤回请求
            response = await self.common_api(path, "DELETE")

            if isinstance(response, OpenAPIErrorCallback):
                # 如果API返回错误，获取错误信息并记录
                error_message = self._get_recall_error_message(response.code)
                logger.error(f"[QQAPI.recallMessage] {error_message}")

                # 记录撤回失败的详细日志
                self._log_message_recall(
                    message_type=target_type.name.lower(),
                    target_id=target_id,
                    message_id=message_id,
                    hide_tip=hide_tip,
                    success=False,
                )
                return False

            # 记录撤回成功的详细日志
            self._log_message_recall(
                message_type=target_type.name.lower(),
                target_id=target_id,
                message_id=message_id,
                hide_tip=hide_tip,
                success=True,
            )
            return True

        except Exception as e:
            # 发生异常时记录详细的错误信息
            error_details = (
                f"[QQAPI.recallMessage] 撤回消息时发生错误:\n"
                f"错误信息: {str(e)}\n"
                f"目标类型: {target_type.name}\n"
                f"目标ID: {target_id}\n"
                f"消息ID: {message_id}"
            )
            logger.error(error_details, style="bold red")

            # 记录撤回失败的详细日志
            self._log_message_recall(
                message_type=target_type.name.lower(),
                target_id=target_id,
                message_id=message_id,
                hide_tip=hide_tip,
                success=False,
            )
            return False

    def _get_recall_error_message(self, error_code: int) -> str:
        """处理撤回消息时的错误码，返回人类可读的错误描述"""
        return {
            304023: "消息发送超过2分钟，无法撤回",
            304024: "没有足够的权限执行撤回操作",
            304025: "消息不存在或已被撤回",
        }.get(error_code, f"撤回消息失败 (错误码: {error_code})")
