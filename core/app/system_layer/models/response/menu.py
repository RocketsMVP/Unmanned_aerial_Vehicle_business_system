from typing import List

from core import base
from ..menu import MenuSavePydantic, MenuTreePydantic


class MenuListResponse(base.PageInfoResponse):
    list: List[MenuSavePydantic]


class MenuResponse(base.Response):
    data: MenuListResponse


class MenuDataResponse(base.Response):
    data: MenuSavePydantic


class MenuTreeResponse(base.Response):
    data: List[MenuTreePydantic]


class UserMenuResponse(base.Response):
    data: List[MenuSavePydantic]
