from graia.broadcast.entities.event import Dispatchable
from pydantic import BaseModel


class CocotstBaseEvent(BaseModel, Dispatchable):
    """cocotst 基础事件"""
