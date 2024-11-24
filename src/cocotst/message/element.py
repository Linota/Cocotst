from typing import Dict, List, Literal, Optional

import aiofiles
from pydantic import BaseModel


class Element(BaseModel):
    """消息元素"""


class MediaElement(Element):
    """媒体消息元素"""

    data: Optional[bytes] = None
    """媒体资源链接"""
    path: Optional[str] = None
    """媒体资源路径"""
    type: Literal["image", "video", "voice", 4]
    """媒体资源类型"""

    def __init__(self, data: Optional[bytes] = None, path: Optional[str] = None):
        try:
            assert data or path
        except AssertionError:
            raise ValueError("data 和 path 不能同时为空")
        super().__init__(data=data, path=path)

    async def as_data_bytes(self):
        """将媒体资源转换为 bytes"""
        if self.data:
            return self.data
        else:
            async with aiofiles.open(self.path, "rb") as f:
                return await f.read()


class Image(MediaElement):
    """图片消息元素"""

    type: Literal["image"] = "image"


class Video(MediaElement):
    """视频消息元素"""

    type: Literal["video"] = "video"


class Voice(MediaElement):
    """语音消息元素"""

    type: Literal["voice"] = "voice"


class File(MediaElement):
    """文件消息元素"""

    type: Literal[4] = 4

    def __init__(self, url: Optional[str] = None, path: Optional[str] = None):
        raise NotImplementedError("文件消息元素暂不支持")


class Markdown(Element):
    """Markdown 消息元素"""

    content: str
    """原生 markdown 文本内容"""
    custom_template_id: str
    """markdown 模版id，申请模版后获得"""
    params: List[Dict]
    """{key: xxx, values: xxx}，模版内变量与填充值的kv映射"""


class Embed(Element): ...  # Incomplete


class Ark(Element): ...  # Incomplete
