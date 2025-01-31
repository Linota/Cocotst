from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ButtonRenderData(BaseModel):
    """按钮渲染数据"""
    
    label: str = Field(..., description="按钮上的文字")
    visited_label: str = Field(..., description="点击后按钮上的文字")
    style: int = Field(..., description="按钮样式：0 灰色线框，1 蓝色线框")

class ButtonPermission(BaseModel):
    """按钮权限设置"""
    
    type: int = Field(..., description="0 指定用户可操作，1 仅管理者可操作，2 所有人可操作，3 指定身份组可操作")
    specify_user_ids: Optional[List[str]] = Field(None, description="有权限的用户 id 的列表")
    specify_role_ids: Optional[List[str]] = Field(None, description="有权限的身份组 id 的列表（仅频道可用）")

class ButtonAction(BaseModel):
    """按钮动作设置"""
    
    type: int = Field(..., description="0 跳转按钮，1 回调按钮，2 指令按钮")
    permission: ButtonPermission = Field(..., description="按钮权限配置")
    data: str = Field(..., description="操作相关的数据")
    reply: Optional[bool] = Field(False, description="指令按钮可用，指令是否带引用回复本消息")
    enter: Optional[bool] = Field(False, description="指令按钮可用，点击按钮后直接自动发送 data")
    anchor: Optional[int] = Field(None, description="指令按钮下有效，1时唤起选图器")
    unsupport_tips: str = Field(..., description="客户端不支持本action时的提示文案")

class Button(BaseModel):
    """消息按钮"""
    
    id: Optional[str] = Field(None, description="按钮ID：在一个keyboard消息内设置唯一")
    render_data: ButtonRenderData = Field(..., description="按钮渲染数据")
    action: ButtonAction = Field(..., description="按钮动作设置")

class ButtonRow(BaseModel):
    """按钮行"""
    
    buttons: List[Button] = Field(..., max_items=5, description="单行最多5个按钮")

class KeyboardContent(BaseModel):
    """按钮内容"""
    
    rows: List[ButtonRow] = Field(..., max_items=5, description="最多5行按钮")

