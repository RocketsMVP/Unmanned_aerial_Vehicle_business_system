from fastapi import APIRouter, FastAPI, Query, Body, Response

from core import base
from ..models import request, UserAllPydantic, UserAlreadyExistsError, UserUpdatePydantic, response
from ..models.response import UserResponse, UserDataResponse, UserTokenResponse
from ..service.user import user_service


class UserRouter(base.Assembly):

    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/user", tags=["用户管理"])
        self._setup_routes()

    def _setup_routes(self):

        @self.router.get(
            "/list",
            summary="用户列表",
            response_model=UserResponse | base.Response
        )
        async def get_user_list(page_info: request.UserSearch = Query()):
            try:
                data, count = await user_service.get_user_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/according_token_obtain',
            summary="访问令牌获取菜单权限信息",
            response_model=response.UserMenuResponse | base.Response
        )
        async def according_token_obtain():
            user = self.with_value('user')
            try:
                data = await user_service.according_token_obtain(user['role'])
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/according_token_basic',
            summary="访问令牌获取用户详情",
            response_model=UserTokenResponse | base.Response
        )
        async def get_user():
            uid = self.with_value('uid')
            try:
                data = await user_service.get_user(int(uid))
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/{id}',
            summary="用户详情",
            response_model=UserDataResponse | base.Response
        )
        async def get_user(id: int):
            try:
                data = await user_service.get_user(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.post(
            "/create",
            summary="创建用户",
            response_model=UserDataResponse | base.Response
        )
        async def create_user(user: UserAllPydantic = Body()):
            try:
                data = await user_service.create_user(user)
                return self.success_correctly_data(data, "创建成功")
            except UserAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("创建失败")

        @self.router.put(
            "/update",
            summary="更新用户",
            response_model=base.Response
        )
        async def update_user(user: UserUpdatePydantic = Body()):
            try:
                await user_service.update_user(user)
                return self.success_correctly("更新成功")
            except UserAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.put(
            "/update_information",
            summary="更新用户基本信息",
            response_model=base.Response
        )
        async def update_user(user: UserUpdatePydantic = Body()):
            try:
                user.id = int(self.with_value('uid'))
                await user_service.update_user(user)
                return self.success_correctly("更新成功")
            except UserAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.delete(
            "/delete",
            summary="删除用户",
            response_model=base.Response
        )
        async def delete_user(info: base.GetById = Body()):
            try:
                await user_service.delete_user(info.id)
                return self.success_correctly("删除成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("删除失败")


user_router = UserRouter()
