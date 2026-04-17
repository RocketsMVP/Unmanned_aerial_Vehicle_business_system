from core import base
from ..document import DocumentPydantic


class DocumentSearch(base.PageInfo, DocumentPydantic):
    start_time: str | None = base.Field(None, description="开始时间")
    end_time: str | None = base.Field(None, description="结束时间")
