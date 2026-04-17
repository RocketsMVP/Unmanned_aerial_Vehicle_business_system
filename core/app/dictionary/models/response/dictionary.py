from typing import List, Dict, Any
from core.base import Response, PageInfoResponse, BaseModel
from ..dictionary import DictionaryPydantic


class DictionaryListResponse(PageInfoResponse):
    list: List[DictionaryPydantic]


class DictionaryResponse(Response):
    data: DictionaryListResponse


class DictionaryDataResponse(Response):
    data: DictionaryPydantic


class DictionaryPublicResponse(Response):
    data: List[Dict[str, Any]]


# 定义 channel.data 中每个字典的结构
class ChannelItem(BaseModel):
    id: int
    name: str


# 定义 model_type 和 channel 的结构
class DictionaryItem(BaseModel):
    type: str
    data: Dict[str, str] | List[ChannelItem]  # 使用 Union 支持 Dict 和 List


# 定义整体响应模型
class DictResponse(Response):
    data: Dict[str, DictionaryItem]
