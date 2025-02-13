from pydantic import BaseModel,RootModel
from typing import List, Optional
import launart
from cocotst.network.services import HttpxClientSessionService

class Attachment(BaseModel):
    id: Optional[str] = "C2CNOID"
    url: str
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    size: int
    content_type: str

    async def to_data_bytes(self) -> bytes:
        if self.url:
            session = launart.Launart.current().get_component(HttpxClientSessionService).async_client
            # check url scheme
            if self.url.startswith("http"):
                return (await session.get(self.url)).content
            else:
                return (await session.get("http://" + self.url)).content

class Attachments(RootModel[List[Attachment]]):
    """消息附件"""

    @property
    def attachments(self):
        return self.root