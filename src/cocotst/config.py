from typing import Optional

from pydantic import BaseModel


class WebHookDebugConfig(BaseModel):
    print_webhook_data: bool = True
    """打印webhook数据"""

class ApiCallDebugConfig(BaseModel):
    ssl_verify: bool = False
    """是否验证ssl证书"""


class DebugConfig(BaseModel):
    webhook: WebHookDebugConfig = WebHookDebugConfig()
    api_call: ApiCallDebugConfig = ApiCallDebugConfig()


class DebugFlag(BaseModel):
    debug_flag: bool = False
    checked_debug_flags: bool = False
    debug_config: Optional[DebugConfig] = None
