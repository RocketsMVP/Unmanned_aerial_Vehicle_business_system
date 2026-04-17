from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from core.base import models


class Document(models.Model):
    __tablename__ = "document"
    __table_args__ = {
        "comment": "文件管理"
    }

    name: Mapped[str | None] = mapped_column(String(255), comment="文件名称")
    file_md5: Mapped[str | None] = mapped_column(String(255), comment="文件md5")
    path: Mapped[str | None] = mapped_column(String(255), comment="文件路径")
    tag: Mapped[str | None] = mapped_column(String(255), comment="标签")
    size: Mapped[int | None] = mapped_column(Integer, comment="文件大小")
    chunk_total: Mapped[int | None] = mapped_column(comment="文件切片总数")

    is_done: Mapped[bool | None] = mapped_column(default=False, comment="是否完成")
    # --- 通用外键 (Generic Foreign Key) 的实现 ---
    # 1. 存储所有者记录的主键。注意：这里没有 ForeignKey() 约束！
    #    类型应该是你系统中主键的通用类型（比如 Integer 或 String/UUID）
    owner_id: Mapped[int | None] = mapped_column(Integer, comment="所有者ID")

    # 2. 存储所有者模型的类型/表名
    owner_type: Mapped[str | None] = mapped_column(String(50), comment="所有者类型 (表名)")


DocumentPydantic = models.model_creator(Document, exclude=("deleted_at",))
DocumentListPydantic = models.model_creator(Document, exclude=(
    "deleted_at", 'path', 'file_md5', 'chunk_total', 'is_done', 'owner_id', 'owner_type'))


class ChunkFile(models.Model):
    """分片上传任务（简化版）"""
    __tablename__ = "chunk_file"
    __table_args__ = {
        "comment": "分片上传任务"
    }

    file_number: Mapped[int] = mapped_column(comment="文件分片序号")
    order_id: Mapped[int] = mapped_column(comment="上级 ID")
    file_md5: Mapped[str] = mapped_column(String(100), comment="文件MD5值")
    path: Mapped[str] = mapped_column(String(500), comment="文件存储路径")


ChunkFilePydantic = models.model_creator(Document, exclude=("deleted_at",))
