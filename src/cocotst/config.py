from typing import Optional

from pydantic import BaseModel


class WebHookDebugConfig(BaseModel):
    print_webhook_data: bool = True


class DebugConfig(BaseModel):
    webhook: WebHookDebugConfig = WebHookDebugConfig()


class DebugFlag(BaseModel):
    debug_flag: bool = False
    checked_debug_flags: bool = False
    debug_config: Optional[DebugConfig] = None
