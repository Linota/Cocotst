from typing import Optional

from pydantic import BaseModel


class Target(BaseModel):
    """回复目标"""

    target_unit: Optional[str] = None
    """精确的 openid , 群消息的时候是群的 openid , 私聊消息的时候是用户的 openid"""
    target_id: Optional[str] = None
    """被动回复消息的时候需要的消息 id"""
    event_id: Optional[str] = None
    """非用户主动事件触发的时候需要的 event_id"""