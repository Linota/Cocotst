from typing import Optional

from pydantic import BaseModel


class WebHookDebugConfig(BaseModel):
    """WebHook 相关 Debug 配置"""

    print_webhook_data: bool = True
    """打印webhook数据"""


class DebugConfig(BaseModel):
    webhook: WebHookDebugConfig = WebHookDebugConfig()


class DebugFlag(BaseModel):
    debug_flag: bool = False
    checked_debug_flags: bool = False
    debug_config: Optional[DebugConfig] = None
