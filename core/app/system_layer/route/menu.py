from fastapi import APIRouter, Query, Body

from core import base
from ..models import request, MenuSavePydantic, MenuAlreadyExistsError
from ..models.response import MenuResponse, MenuDataResponse, MenuTreeResponse
from ..service.menu import menu_service


class MenuRouter(base.Assembly):

    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/menu", tags=["菜单管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/list",
            summary="菜单列表",
            response_model=MenuResponse | base.Response
        )
        async def get_menu_list(page_info: request.UserSearch = Query()):
            try:
                data, count = await menu_service.get_menu_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/tree',
            summary="菜单树壮图",
            response_model=MenuTreeResponse | base.Response
        )
        async def get_tree_menu():
            try:
                data = await menu_service.get_tree_menu()
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/{id}',
            summary="菜单详情",
            response_model=MenuDataResponse | base.Response
        )
        async def get_menu(id: int):
            try:
                data = await menu_service.get_menu(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.post(
            "/create",
            summary="创建菜单",
            response_model=MenuDataResponse | base.Response
        )
        async def create_menu(menu: MenuSavePydantic = Body()):
            try:
                data = await menu_service.create_menu(menu)
                return self.success_correctly_data(data, "创建成功")
            except MenuAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("创建失败")

        @self.router.put(
            "/update",
            summary="更新菜单",
            response_model=base.Response
        )
        async def update_menu(user: MenuSavePydantic = Body()):
            try:
                await menu_service.update_menu(user)
                return self.success_correctly("更新成功")
            except MenuAlreadyExistsError as e:
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.delete(
            "/delete",
            summary="删除菜单",
            response_model=base.Response
        )
        async def delete_menu(info: base.GetById = Body()):
            try:
                await menu_service.delete_menu(info.id)
                return self.success_correctly("删除成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("删除失败")


menu_router = MenuRouter()
