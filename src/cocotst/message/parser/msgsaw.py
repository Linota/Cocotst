from typing import List, Optional, Tuple, Union
from pydantic import BaseModel, Field
from graia.broadcast.entities.dispatcher import BaseDispatcher
from cocotst.event.message import MessageEvent
from cocotst.network.model.webhook import Content
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.interfaces.dispatcher import DispatcherInterface


class Main(BaseModel):
    """主命令定义"""

    match: str = Field(description="匹配的命令")
    alt_match: List[str] = Field(default_factory=list, description="替代匹配命令列表")
    need_argv: bool = Field(default=False, description="是否需要参数")
    lack_argv_stop: bool = Field(default=False, description="缺少参数时是否停止执行")


class Sub(BaseModel):
    """子命令定义"""

    match: str = Field(description="匹配的子命令")
    alt_match: List[str] = Field(default_factory=list, description="替代匹配子命令列表")
    need_argv: bool = Field(default=False, description="是否需要参数")
    lack_argv_stop: bool = Field(default=False, description="缺少参数时是否停止执行")


class QSubResult(BaseModel):
    """QSubCommandMatcher 的结果"""

    raw: str = Field(description="原始命令字符串")
    command: str = Field(description="主命令 (e.g. '井')")
    subcommand: str = Field(description="子命令 (e.g. '开')")
    remaining: str = Field(description="剩余内容")
    length: int = Field(description="命令长度 (包含主命令和子命令)")
    main_argv: str = Field(default="", description="主命令的参数")
    sub_argv: str = Field(default="", description="子命令的参数")
    original_sub: Optional[str] = Field(default=None, description="原始子命令（匹配到的主要或替代命令）")

    def get_segments(self) -> List[str]:
        """获取所有命令块 (按空格分割)"""
        return [seg for seg in self.remaining.split() if seg]

    def get_segment(self, index: int) -> Optional[str]:
        """获取指定位置的命令块"""
        segments = self.get_segments()
        return segments[index] if 0 <= index < len(segments) else None

    @property
    def has_remaining(self) -> bool:
        """是否还有剩余内容"""
        return bool(self.remaining.strip())

    @property
    def match_main(self) -> bool:
        """是否匹配到主命令"""
        return self.length > 0

    def match_main_command(self, main_match: str) -> bool:
        """检查是否匹配特定的主命令"""
        return self.command == main_match

    @property
    def match_sub(self) -> bool:
        """是否匹配到子命令"""
        return bool(self.subcommand)

    def match_sub_command(self, sub_match: str) -> bool:
        """检查是否匹配特定的子命令
        传入主要命令，如果匹配到主要命令或其任何替代命令都返回True"""
        return self.subcommand == sub_match

    @property
    def is_pure_main(self) -> bool:
        """是否仅匹配到主命令"""
        return self.match_main and not self.match_sub


class MessageSaw(BaseDispatcher):
    """MessageSaw 匹配器,简易命令解析工具"""

    def __init__(
        self,
        command: Union[str, Main],
        subcommands: Optional[List[Union[str, Sub]]] = None,
    ) -> None:
        # 处理主命令
        if isinstance(command, str):
            self.main = Main(match=command)
        else:
            self.main = command

        # 处理子命令
        self.subs: List[Sub] = []
        if subcommands:
            for sub in subcommands:
                if isinstance(sub, str):
                    self.subs.append(Sub(match=sub))
                else:
                    self.subs.append(sub)

        # 生成匹配模式
        self.patterns: List[Tuple[str, str, str, str]] = []  # pattern, cmd, subcmd, original_sub
        self.base_patterns: List[Tuple[str, str]] = []

        # 主命令匹配模式，包含原始match和alt_match
        all_main_matches = [self.main.match] + self.main.alt_match
        for main_match in all_main_matches:
            prefixes = [f"/{main_match}", main_match]
            for prefix in prefixes:
                # 主命令模式
                self.base_patterns.append((prefix, main_match))
                # 子命令模式
                for sub in self.subs:
                    # 所有子命令都映射到主要match
                    all_sub_matches = [sub.match] + sub.alt_match
                    for sub_match in all_sub_matches:
                        pattern = f"{prefix}{sub_match}"
                        self.patterns.append((pattern, main_match, sub.match, sub_match))

    async def cmd(self, content: Content) -> Optional[QSubResult]:
        raw_content = content.content
        content_str = raw_content.replace(" ", "")

        # 先尝试匹配带子命令的模式
        for pattern, cmd, subcmd, original_sub in self.patterns:
            if content_str.startswith(pattern):
                remaining = content_str[len(pattern) :].strip()
                # 检查子命令是否需要参数
                sub = next(sub for sub in self.subs if sub.match == subcmd)
                if sub.need_argv and not remaining and sub.lack_argv_stop:
                    raise ExecutionStop
                return QSubResult(
                    raw=raw_content,
                    command=cmd,
                    subcommand=subcmd,
                    remaining=remaining,
                    length=len(pattern),
                    main_argv="",  # 子命令模式下主命令参数为空
                    sub_argv=remaining,  # 子命令的参数
                    original_sub=original_sub,  # 保存原始匹配到的子命令
                )

        # 如果没匹配到子命令，尝试匹配主命令
        for pattern, cmd in self.base_patterns:
            if content_str.startswith(pattern):
                remaining = content_str[len(pattern) :].strip()
                # 检查主命令是否需要参数
                if self.main.need_argv and not remaining and self.main.lack_argv_stop:
                    raise ExecutionStop
                return QSubResult(
                    raw=raw_content,
                    command=cmd,
                    subcommand="",
                    remaining=remaining,
                    length=len(pattern),
                    main_argv=remaining,  # 主命令的参数
                    sub_argv="",  # 没有子命令，子命令参数为空
                )

        raise ExecutionStop

    async def catch(self, interface: DispatcherInterface[MessageEvent]):
        if interface.annotation == QSubResult:
            result = await self.cmd(interface.event.content)
            if result is not None:
                return result
