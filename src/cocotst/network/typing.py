from pydantic import BaseModel
from typing import DefaultDict


class OpenAPIResponse(DefaultDict[str, str]): ...
