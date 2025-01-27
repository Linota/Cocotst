# 本文件定义了 cocotst 网络模块的有关 频道 专有的数据模型

from typing import List, Optional

from pydantic import BaseModel,RootModel
from aiohttp.client import ClientSession





class Mention(BaseModel):
    id: str
    username: str
    avatar: str
    bot: bool


class Member(BaseModel):
    nick: Optional[str] = None
    roles: Optional[List[str]] = None
    joined_at: Optional[str] = None
