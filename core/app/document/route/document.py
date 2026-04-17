from mimetypes import guess_type

import fastapi
from fastapi import APIRouter, Query, Body, UploadFile, File

from core import base
from ..models import request, DocumentPydantic
from ..models.response import (
    DocumentResponse, DocumentDataResponse,
    ChunkInitResponse, ChunkUploadResponse
)
from ..service.document import document_service
from ...system_layer.service.jwt import EXCLUDED_ROUTES

MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentRoute(base.Assembly):
    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/document", tags=["文件管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/list",
            summary="文件列表",
            response_model=DocumentResponse | base.Response,
        )
        async def list_documents(page_info: request.DocumentSearch = Query()):
            try:
                data, count = await document_service.get_document_list(page_info)
                return self.success_correctly_data(
                    self.page_result(data, count, page_info.page, page_info.page_size), "查询成功"
                )
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.get(
            "/{id}",
            summary="文件详情",
            response_model=DocumentDataResponse | base.Response,
        )
        async def get_document(id: int):
            try:
                data = await document_service.get_document(id)
                return self.success_correctly_data(data, "查询成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("查询失败")

        @self.router.post(
            "/upload",
            summary="文件上传",
            response_model=DocumentDataResponse | base.Response,
        )
        async def create_document(file: UploadFile = File(...)):
            try:
                if file.size > MAX_FILE_SIZE:
                    return self.fail_correctly("文件过大")
                data = await document_service.create_document(file)
                return self.success_correctly_data(data, "上传成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("上传失败")

        @self.router.get(
            "/rendering/{path}",
            summary="文件渲染",
        )
        async def rendering_document(path: str):
            try:
                headers = {"Content-Disposition": "inline"}
                if ".mp4" in path:
                    headers.update({"Content-Type": "video/mp4"})
                if not path:
                    return self.fail_correctly("文件不存在")
                media_type, _ = guess_type(path)
                if not media_type:
                    media_type = "application/octet-stream"  # 默认二进制流
                # 使用存储实例读取文件
                file_content = document_service.get_storage().read_file(path)
                return fastapi.Response(content=file_content, media_type=media_type, headers=headers)
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("文件不存在")

        @self.router.post(
            "/chunk/init",
            summary="初始化分片上传",
            response_model=ChunkInitResponse | base.Response,
        )
        async def init_chunk_upload(info: request.DocumentPydantic = Body(...)):
            """初始化大文件分片上传，返回上传任务ID"""
            try:
                data = await document_service.init_chunk_upload(info)
                return self.success_correctly_data(data, "初始化成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly(f"初始化失败: {str(e)}")

        @self.router.post(
            "/chunk/upload",
            summary="上传分片",
            response_model=ChunkUploadResponse | base.Response,
        )
        async def upload_chunk(
                file_id: int = Body(..., description="文件ID"),
                file_md5: str = Body(..., description="文件MD5值"),
                file_number: int = Body(..., description="分片序号（从1开始）"),
                chunk: UploadFile = File(..., description="分片文件")
        ):
            """上传单个分片（支持断点续传，已上传的分片会自动跳过）"""
            try:

                data = await document_service.upload_chunk(file_id, file_md5, file_number, chunk)
                return self.success_correctly_data(data, "分片上传成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly(f"分片上传失败: {str(e)}")

        @self.router.post(
            "/chunk/complete",
            summary="完成分片上传",
            response_model=ChunkInitResponse | base.Response,
        )
        async def complete_chunk_upload(
                file_id: int = Body(..., description="文件ID"),
                file_md5: str = Body(..., description="文件MD5值"),
        ):
            """完成分片上传，合并所有分片并创建文档记录"""
            try:
                data = await document_service.complete_chunk_upload(file_id, file_md5)
                return self.success_correctly_data(data, "上传完成")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly(f"完成上传失败: {str(e)}")


document_route = DocumentRoute()
EXCLUDED_ROUTES.append("/document/rendering")
