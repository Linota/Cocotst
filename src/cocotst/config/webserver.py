from pydantic import BaseModel


class WebHookConfig(BaseModel):
    """webhook 配置"""

    host: str = "0.0.0.0"
    """webhook 的 host"""
    port: int = 2077
    """webhook 的 port"""
    postevent: str = "/postevent"
    """webhook 的 postevent url"""


class FileServerConfig(BaseModel):
    localpath: str = None
    """本地文件路径"""
    remote_url: str = "/fileserver"
    """远程文件路径"""
