from fastapi import APIRouter, Query

from core import base
from ..models import request
from ..models.response import APIResponse, APIDataResponse
from ..service.api import api_service


class ApiRouter(base.Assembly):

    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/api", tags=["路由管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/list",
            summary="路由列表",
            response_model=APIResponse | base.Response
        )
        async def get_api_list(page_info: request.APISearch = Query()):
            try:
                data, count = await api_service.get_api_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            '/{id}',
            summary="路由详情",
            response_model=APIDataResponse | base.Response
        )
        async def get_api(id: int):
            try:
                data = await api_service.get_api(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")


api_router = ApiRouter()
