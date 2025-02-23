from typing import Optional

from pydantic import BaseModel


class Target(BaseModel):
    """回复目标"""

    target_unit: str = ""
    """精确的 openid , 群消息的时候是群的 openid , 私聊消息的时候是用户的 openid"""
    target_id: str = ""
    """被动回复消息的时候需要的消息 id"""
    event_id: str = ""
    """非用户主动事件触发的时候需要的 event_id"""