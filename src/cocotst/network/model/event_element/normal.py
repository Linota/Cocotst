# 本文件定义了 cocotst 网络模块的有关 QQ群聊 和 C2C 专有的数据模型

from typing import Optional
from pydantic import BaseModel
from cocotst.network.model.target import Target
from aiohttp.client import ClientSession

class MessageScene(BaseModel):
    """消息场景"""

    source: str


class Group(BaseModel):
    """群组信息"""

    group_id: str
    group_openid: str

    @property
    def target(self):
        return Target(target_unit=self.group_openid)


class Member(BaseModel):
    """群成员信息"""

    member_openid: str
