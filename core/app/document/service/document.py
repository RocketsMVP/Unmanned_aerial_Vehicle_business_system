import hashlib
import os


from fastapi import UploadFile
from sqlalchemy import select, func, delete

from core import base
from ..models import request, response, Document, DocumentPydantic, ChunkFile
from datetime import datetime, timedelta


class DocumentService(base.Assembly):

    def __init__(self):
        super().__init__()

    async def get_document_list(self, info: request.DocumentSearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(Document)
            if info.name:
                db = db.where(Document.name.like(f'%{info.name}%'))
            if info.start_time:
                db = db.where(Document.created_at >= info.start_time)
            if info.end_time:
                db = db.where(Document.created_at <= info.end_time)
            count = await session.scalar(
                select(func.count()).select_from(Document).where(*db._where_criteria)
            )
            data = await session.scalars(
                db.limit(limit).offset(offset)
            )
            return data.all(), count

    async def get_document(self, id: int):
        async with self.get_db() as session:
            data = await session.scalars(select(Document).where(Document.id == id))
        return data.first()

    async def get_file_content(self, id: int) -> bytes:
        """
        根据文档ID获取文件内容
        :param id: 文档ID
        :return: 文件内容
        """
        document = await self.get_document(id)
        if not document:
            raise ValueError(f"文档不存在: {id}")

        # 使用选定的存储策略读取文件
        return self.get_storage().read_file(document.path)

    async def create_document(self, file: UploadFile):
        md5 = hashlib.md5()
        content = await file.read()
        md5.update(content)
        suffix, trim_suffix, tag = self.filename_handling(file.filename)
        # 生成文件名：MD5(原文件名) + 时间戳 + 后缀
        file_md5 = self.md5v(trim_suffix.encode()) + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + suffix
        # 使用存储类保存文件，存储类会自己处理路径生成
        path = self.get_storage().save_file(file_md5, content, tag)
        doc = Document(
            name=file.filename,
            path=path,
            file_md5=md5.hexdigest(),
            size=len(content),  # UploadFile 没有 size 属性，使用内容长度
            tag=tag,
            is_done=True
        )
        async with self.get_db() as db:
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
        return doc

    def filename_handling(self, file_name: str):
        """
        处理文件名，提取后缀、标签等信息。
        Args:
            file_name (str): 输入文件名
        Returns:
            tuple: (suffix, trim_suffix, tag)
        Raises:
            ValueError: 如果无法提取文件后缀
        """
        # 提取文件后缀
        suffix = os.path.splitext(file_name)[1]  # 例如 ".pdf"
        if not suffix:
            self.S().error("无法提取文件后缀: %s", file_name)
            raise ValueError(f"无法提取文件后缀: {file_name}")

        # 提取标签（去掉点号后的部分）
        tag = suffix[1:]  # 例如 "pdf"

        # 移除文件名的后缀
        trim_suffix = os.path.splitext(file_name)[0]

        return suffix, trim_suffix, tag

    def _get_chunk_path(self, upload_id: str) -> str:
        """获取分片的本地存储路径（统一存储在本地临时目录）"""
        data_dir = self.get_viper().get("system.data-dir", "./data_dir")
        temp_dir = os.path.join(data_dir, "temp", "chunks", upload_id)
        return temp_dir

    def _save_chunk_direct(self, upload_id: str, chunk_number: int, chunk_data: bytes) -> str:
        """直接保存分片到本地临时目录"""
        temp_dir = self._get_chunk_path(upload_id)
        chunk_path = os.path.join(temp_dir, f"{upload_id}_{chunk_number}")
        os.makedirs(os.path.dirname(chunk_path), exist_ok=True, mode=0o755)
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        return chunk_path

    def _cleanup_upload_temp(self, upload_id: str):
        """清理上传任务的所有临时分片"""
        data_dir = self.get_viper().get("system.data-dir", "./data_dir")
        temp_dir = os.path.join(data_dir, "temp", "chunks", upload_id)
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def init_chunk_upload(self, info: DocumentPydantic):
        """
        初始化分片上传（支持断点续传）
        """
        async with self.get_db() as db:
            existing_task = await db.scalar(
                select(Document).where(Document.file_md5 == info.file_md5)
            )
            if existing_task:
                # 如果任务已存在，返回现有信息
                return existing_task
            upload_task = Document(**info.model_dump(exclude_unset=True))
            db.add(upload_task)
            await db.commit()
            await db.refresh(upload_task)

        return upload_task

    async def upload_chunk(self, file_id: int, file_md5: str, file_number: int, chunk: UploadFile):
        """
        上传单个分片（支持断点续传）
        """
        # 检查文件是否存在
        async with self.get_db() as db:
            file = await db.scalar(
                select(ChunkFile).where(ChunkFile.order_id == file_id, ChunkFile.file_md5 == file_md5,
                                        ChunkFile.file_number == file_number)
            )
            if file:
                return file
            chunk_data = await chunk.read()
            # 保存分片到本地文件系统
            # chunk_path = self._get_chunk_path(file_md5, file_number)
            chunk_path = self._save_chunk_direct(file_md5, file_number, chunk_data, )
            # os.makedirs(os.path.dirname(chunk_path), exist_ok=True)
            # with open(chunk_path, "wb") as f:
            #     f.write(chunk_data)
            #     # 保存分片记录到数据库
            chunk_record = ChunkFile(
                file_md5=file_md5,
                file_number=file_number,
                order_id=file_id,
                path=chunk_path,
            )
            db.add(chunk_record)
            await db.commit()
            await db.refresh(chunk_record)
        return chunk_record

    async def complete_chunk_upload(self, file_id: int, file_md5: str):
        """
        完成分片上传，合并所有分片并创建文档记录
        """
        async with self.get_db() as db:
            upload_task = await db.scalar(
                select(Document).where(Document.id == file_id, Document.file_md5 == file_md5)
            )
            if not upload_task:
                raise ValueError(f"上传任务不存在: {file_id}")

            # 合并所有分片
            chunk_path = self._get_chunk_path(file_md5)
            all_files = os.listdir(chunk_path)
            merged_content = b""
            for i in range(1, len(all_files) + 1):
                chunk_file = os.path.join(chunk_path, f"{file_md5}_{i}")
                with open(chunk_file, "rb") as f:
                    chunk_data = f.read()
                    merged_content += chunk_data

            # 保存合并后的文件（使用存储层的基础方法）
            storage = self.get_storage()
            file_name = datetime.now().strftime(f"{file_md5}_%Y%m%d%H%M%S.{upload_task.tag}")
            path = storage.save_file(file_name, merged_content, upload_task.tag)

            # 清理所有临时分片
            self._cleanup_upload_temp(file_md5)

            # 创建文档记录

            upload_task.is_done = True
            upload_task.path = path

            # 删除上传任务记录
            await db.execute(
                delete(ChunkFile).where(ChunkFile.order_id == file_id, ChunkFile.file_md5 == file_md5)
            )

            await db.commit()
            await db.refresh(upload_task)

        return upload_task


document_service = DocumentService()
