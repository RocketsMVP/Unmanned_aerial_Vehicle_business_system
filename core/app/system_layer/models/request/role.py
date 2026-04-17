from core import base
from ..role import RolePydantic


class RoleSearch(base.PageInfo, RolePydantic, base.TimeInfo):
    pass


class CasbinReq(base.BaseModel):
    code: str
    checked: list[str]


class CasbinAPI(base.BaseModel):
    code: str
    checked: list[dict[str, str]]
