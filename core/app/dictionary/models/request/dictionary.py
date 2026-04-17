from typing import List

from core.base.models import PageInfo, BaseModel
from ..dictionary import DictionaryPydantic


class DictionarySearch(PageInfo, DictionaryPydantic):
    pass


class DictionaryListSearch(BaseModel):
    code: List[str]
