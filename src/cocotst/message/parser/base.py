"""Cocotst 基础的 parser, 包括 DetectPrefix 与 DetectSuffix, Modified from Graia Ariadne"""

import abc
from typing import Iterable, List, Optional, Union

from graia.broadcast.builtin.derive import Derive
from graia.broadcast.entities.decorator import Decorator
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.interfaces.decorator import DecoratorInterface
from graia.broadcast.interfaces.dispatcher import DispatcherInterface

from cocotst.network.model.webhook import Content


class ContentDecorator(abc.ABC, Decorator, Derive[Content]):
    pre = True

    @abc.abstractmethod
    async def __call__(self, content: Content, interface: DispatcherInterface) -> Optional[Content]: ...

    async def target(self, interface: DecoratorInterface):
        return await self(
            await interface.dispatcher_interface.lookup_param("content", Content, None),
            interface.dispatcher_interface,
        )


class DetectPrefix(ContentDecorator):
    """前缀检测器"""

    def __init__(self, prefix: Union[str, Iterable[str]]) -> None:
        """初始化前缀检测器.

        Args:
            prefix (Union[str, Iterable[str]]): 要匹配的前缀
        """
        self.prefix: List[str] = [prefix] if isinstance(prefix, str) else list(prefix)

    async def __call__(self, content: Content, _) -> Optional[Content]:
        for prefix in self.prefix:
            if content.content.startswith(prefix):
                return Content(content.content.removeprefix(prefix).removeprefix(" "))

        raise ExecutionStop


class DetectSuffix(ContentDecorator):
    """后缀检测器"""

    def __init__(self, suffix: Union[str, Iterable[str]]) -> None:
        """初始化后缀检测器.

        Args:
            suffix (Union[str, Iterable[str]]): 要匹配的后缀
        """
        self.suffix: List[str] = [suffix] if isinstance(suffix, str) else list(suffix)

    async def __call__(self, content: Content, _) -> Optional[Content]:
        for suffix in self.suffix:
            if content.content.endswith(suffix):
                return Content(content.content.removesuffix(suffix).removesuffix(" "))

        raise ExecutionStop


class ContainKeyword(ContentDecorator):
    """消息中含有指定关键字"""

    def __init__(self, keyword: str) -> None:
        """初始化

        Args:
            keyword (str): 关键字
        """
        self.keyword: str = keyword

    async def __call__(self, content: Content, _) -> Optional[Content]:
        if self.keyword in content.content:
            return content
        raise ExecutionStop


class QCommandMatcher(ContentDecorator):
    """QCommand 匹配器"""

    def __init__(self, command: str) -> None:
        """初始化

        Args:
            command (str): 要匹配的命令，只需要提供命令本体不用处理 '/' ' '
        """
        commands = [f" /{command}", f"/{command}", f" {command}", command]
        self.commands: List[str] = commands

    async def __call__(self, content: Content, _) -> Optional[Content]:
        for command in self.commands:
            if content.content.startswith(command):
                return Content(content.content.removeprefix(command).removeprefix(" "))

        raise ExecutionStop


StartsWith = DetectPrefix
EndsWith = DetectSuffix
