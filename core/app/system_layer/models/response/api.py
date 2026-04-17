from typing import List

from core import base
from ..api import APIPydantic


class APIListResponse(base.PageInfoResponse):
    list: List[APIPydantic]


class APIResponse(base.Response):
    data: APIListResponse


class APIDataResponse(base.Response):
    data: APIPydantic
