from pydantic import BaseModel


class OpenAPIErrorCallback(BaseModel):
    """OpenAPI 回调"""

    message: str
    """错误信息"""
    code: int
    """错误码"""


class AccessToken(BaseModel):
    access_token: str
    expires_in: int