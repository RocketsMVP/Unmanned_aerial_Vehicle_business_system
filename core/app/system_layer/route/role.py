from fastapi import APIRouter, Query, Body

from core import base
from ..models import request, RolePydantic, RoleAlreadyExistsError, response
from ..models.response import RoleResponse, RoleDataResponse
from ..service.role import role_service


class RoleRouter(base.Assembly):

    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/role", tags=["角色管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/list",
            summary="角色列表",
            response_model=RoleResponse | base.Response
        )
        async def get_role_list(page_info: request.UserSearch = Query()):
            try:
                data, count = await role_service.get_role_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/get_role_permission',
            summary="角色权限",
            response_model=response.RolePermissionResponse | base.Response
        )
        async def get_role_permission(code: str = Query(...)):
            try:
                data = await role_service.get_role_permission(code)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/{id}',
            summary="角色详情",
            response_model=RoleDataResponse | base.Response
        )
        async def get_role(id: int):
            try:
                data = await role_service.get_role(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.post(
            "/create",
            summary="创建角色",
            response_model=RoleDataResponse | base.Response
        )
        async def create_role(menu: RolePydantic = Body()):
            try:
                data = await role_service.create_role(menu)
                return self.success_correctly_data(data, "创建成功")
            except RoleAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("创建失败")

        @self.router.put(
            "/update",
            summary="更新角色",
            response_model=base.Response
        )
        async def update_role(user: RolePydantic = Body()):
            try:
                await role_service.update_role(user)
                return self.success_correctly("更新成功")
            except RoleAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.delete(
            "/delete",
            summary="删除角色",
            response_model=base.Response
        )
        async def delete_role(info: base.GetById = Body()):
            try:
                await role_service.delete_role(info.id)
                return self.success_correctly("删除成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("删除失败")

        @self.router.post(
            "/update_role_menu",
            summary="更新角色菜单权限",
            response_model=base.Response
        )
        async def update_role_menu(info: request.CasbinReq = Body()):
            try:
                await role_service.update_role_menu(info)
                return self.success_correctly("更新成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.post(
            "/update_role_api",
            summary="更新角色API 权限",
            response_model=base.Response
        )
        async def update_role_api(info: request.CasbinAPI = Body()):
            try:
                await role_service.update_role_api(info)
                return self.success_correctly("更新成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")


role_router = RoleRouter()
