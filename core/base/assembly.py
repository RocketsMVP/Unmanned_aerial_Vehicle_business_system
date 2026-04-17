import hashlib
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from core import milvus_client
from core.base.ctx import CTX
from core.base.wrapper import customization_correctly, fail_correctly, fail_correctly_data, success_correctly, success_correctly_data
from core.intra import config
from core.intra import cache
from core.intra import zap
from core.intra.local_storage import LocalStorage
from core.intra.minio_storage import MinioStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class PageInfoResponse(BaseModel):
    list: List = Field(..., description="列表数据")
    total: int = Field(..., description="列表数据总数")
    page_size: int = Field(..., description="每页数量")
    page: int = Field(..., description="页码")


class Assembly:
    __abstract__ = True
    """
    Assembly 类封装了一系列常用方法，方便在 FastAPI 应用中获取配置、数据库连接、缓存、日志等，
    同时也封装了响应返回、MD5 加密、分页结果组装等功能。
    """
    _storage_instance = None  # 类级别的存储实例缓存

    def with_context(self, key: str, value: Any):
        """
        设置上下文，将传入的 cl 存储在上下文中，key 为 "layer"
        """
        CTX.get().update({key: value})

    def with_value(self, key: str) -> Any:
        """
        根据 key 从上下文中获取对应的值
        """
        return CTX.get().get(key)

    def get_viper(self):
        """
        获取配置信息
        """
        return config

    def get_storage(self):
        """
        根据配置动态初始化存储实例（懒加载单例模式）
        :return: 存储实例
        """
        # 如果已经初始化，直接返回缓存的实例
        if Assembly._storage_instance is not None:
            return Assembly._storage_instance
        
        # 根据配置决定初始化哪个存储类
        storage_type = self.get_viper().get_string('system.storage-type')
        if storage_type == 'minio':
            Assembly._storage_instance = MinioStorage()
        else:
            Assembly._storage_instance = LocalStorage()
        
        return Assembly._storage_instance

    @asynccontextmanager
    async def get_db(self, hard_delete=False) -> AsyncSession:
        """
        获取数据库连接
        """
        # 延迟导入，避免循环导入
        from core.db import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                session.info['hard_delete'] = hard_delete
                yield session
            except Exception as e:
                await session.rollback()
                self.S().error(e)
                raise e

    def get_milvus(self):
        """
        获取 Milvus 客户端（动态创建，线程本地）
        """
        return milvus_client


    def get_engine(self):
        # 延迟导入，避免循环导入
        from core.db import async_engine
        return async_engine

    def get_cache(self):
        """
        获取缓存实例
        """
        return cache

    def S(self) -> logging.Logger:
        """
        获取日志记录器，返回一个 logger 实例
        """
        return zap.logger

    def md5v(self, s_bytes: bytes, extra: bytes = b"") -> str:
        """
        返回传入字节串的 MD5 十六进制摘要，可接收额外字节进行附加（可选）。
        """
        m = hashlib.md5()
        m.update(s_bytes)
        digest = m.hexdigest()
        # 如果需要将 extra 字节加到摘要后面，可进行转换，这里简单示例：
        if extra:
            digest += extra.decode("utf-8", errors="ignore")
        return digest

    def models(self) -> Dict[str, Any]:
        """
        返回项目中所有模型的集合
        """
        return self.env

    def fail_correctly_data(self, data: Any, message: str) -> JSONResponse:
        """
        返回带数据的失败响应
        """
        return fail_correctly_data(data, message)

    def success_correctly_data(self, data: Any, message: str) -> JSONResponse:
        """
        返回带数据的成功响应
        """
        return success_correctly_data(data, message)

    def fail_correctly(self, message: str) -> JSONResponse:
        """
        返回不带数据的失败响应
        """
        return fail_correctly(message)

    def success_correctly(self, message: str) -> JSONResponse:
        """
        返回不带数据的成功响应
        """
        return success_correctly(message)

    def page_result(self, list_data: Any, total: int, page: int, page_size: int):
        """
        组装分页返回结果
        """
        return PageInfoResponse(
            list=list_data,
            total=total,
            page_size=page_size,
            page=page
        )

    def _format_sse_event(self, data):
        """格式化为SSE标准事件格式"""
        return json.dumps(data, ensure_ascii=False)
