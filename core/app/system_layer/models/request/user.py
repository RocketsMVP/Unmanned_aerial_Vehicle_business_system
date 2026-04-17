from core import base
from ..user import UserPydantic


class LoginReq(base.BaseModel):
    login: str
    password: str
    captcha: str
    captcha_id: str


class UserSearch(base.PageInfo, UserPydantic, base.TimeInfo):
    pass
