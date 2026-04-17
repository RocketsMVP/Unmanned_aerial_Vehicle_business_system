from pydantic import BaseModel, Field
from typing import List

from .. import ChunkFilePydantic
from .. import DocumentPydantic
from core.base import Response


class ChunkInitResponse(Response):
    """初始化分片上传响应"""
    data: DocumentPydantic


class ChunkUploadResponse(Response):
    """上传分片响应"""
    data: ChunkFilePydantic
