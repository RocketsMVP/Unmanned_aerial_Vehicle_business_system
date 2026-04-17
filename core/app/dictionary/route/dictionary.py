from fastapi import APIRouter, Query, Body
from sqlalchemy import table, text

from core import base
from ..models import DictionaryPydantic, DictionaryAlreadyExistsError
from ..models.request.dictionary import DictionarySearch, DictionaryListSearch
from ..models.response.dictionary import DictionaryResponse, DictionaryDataResponse, DictResponse
from ..service.dictionary import dictionary_service


class DictionaryRoute(base.Assembly):

    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/dictionary", tags=["字典管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/list",
            summary="字典列表",
            response_model=DictionaryResponse | base.Response
        )
        async def get_dictionary_list(page_info: DictionarySearch = Query()):
            try:
                data, count = await dictionary_service.get_dictionary_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功"
                )
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            "/select",
            summary="字典下拉选择",
            response_model=DictResponse
        )
        async def get_dictionary_select(info: DictionaryListSearch = Query()):
            try:
                data = await dictionary_service.get_dictionary_select(info.code)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            "/{id}",
            summary="字典详情",
            response_model=DictionaryDataResponse | base.Response
        )
        async def get_dictionary(id: int):
            try:
                data = await dictionary_service.get_dictionary(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.post(
            "/create",
            summary="创建字典",
            response_model=DictionaryDataResponse | base.Response
        )
        async def create_dictionary(info: DictionaryPydantic = Body()):
            try:
                data = await dictionary_service.create_dictionary(info)
                return self.success_correctly_data(data, "创建成功")
            except DictionaryAlreadyExistsError as e:
                self.S().error(e)
                return self.fail_correctly(e.message)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("创建失败")

        @self.router.put(
            "/update",
            summary="更新字典",
            response_model=base.Response
        )
        async def update_dictionary(info: DictionaryPydantic = Body()):
            try:
                await dictionary_service.update_dictionary(info)
                return self.success_correctly("更新成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("更新失败")

        @self.router.delete(
            "/delete",
            summary="删除字典",
            response_model=base.Response
        )
        async def delete_dictionary(info: base.GetById = Body()):
            try:
                await dictionary_service.delete_dictionary(info.id)
                return self.success_correctly("删除成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("删除失败")


dictionary_route = DictionaryRoute()
