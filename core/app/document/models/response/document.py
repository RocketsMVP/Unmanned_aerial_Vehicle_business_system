from typing import List

from core import base
from ..document import DocumentPydantic


class DocumentListResponse(base.PageInfoResponse):
    list: List[DocumentPydantic]


class DocumentResponse(base.Response):
    data: DocumentListResponse


class DocumentDataResponse(base.Response):
    data: DocumentPydantic
