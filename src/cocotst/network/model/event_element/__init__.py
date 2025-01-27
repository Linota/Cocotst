from pydantic import BaseModel,RootModel
from typing import List, Optional
from aiohttp.client import ClientSession

class Attachment(BaseModel):
    id: Optional[str] = "C2CNOID"
    url: str
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    size: int
    content_type: str

    async def to_data_bytes(self) -> bytes:
        async with ClientSession() as session:
            async with session.get(self.url) as response:
                return await response.read()
            

class Attachments(RootModel[List[Attachment]]):
    """消息附件"""

    @property
    def attachments(self):
        return self.root