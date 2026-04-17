from typing import List, Any, Dict

from core import base
from ..role import RolePydantic


class RoleListResponse(base.PageInfoResponse):
    list: List[RolePydantic]


class RoleResponse(base.Response):
    data: RoleListResponse


class RoleDataResponse(base.Response):
    data: RolePydantic


# 子模型：API 权限
class APIPermission(base.BaseModel):
    path: str
    act: str


# 数据模型：menu 和 api
class RolePermissionData(base.BaseModel):
    menu: List[str]
    api: List[APIPermission]


class RolePermissionResponse(base.Response):
    data: RolePermissionData
