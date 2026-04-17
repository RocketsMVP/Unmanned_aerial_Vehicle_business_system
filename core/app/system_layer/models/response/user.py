from typing import List

from core import base
from ..user import UserPydantic, UserTokenPydantic


class UserListResponse(base.PageInfoResponse):
    list: List[UserPydantic]


class UserResponse(base.Response):
    data: UserListResponse


class UserDataResponse(base.Response):
    data: UserPydantic


class UserTokenResponse(base.Response):
    data: UserTokenPydantic


