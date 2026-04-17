from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.base import models


class DictionaryAlreadyExistsError(Exception):
    def __init__(self, message="编码已存在"):
        self.message = message
        super().__init__(self.message)


class Dictionary(models.Model):
    __tablename__ = "dictionary"
    __table_args__ = {
        "comment": "字典管理"
    }

    name: Mapped[str] = mapped_column(String(255), comment="名称")
    code: Mapped[str | None] = mapped_column(String(255), comment="编码")
    dictionary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="字典内容")
    mold: Mapped[str | None] = mapped_column(String(255), comment="类型")
    model_name: Mapped[str | None] = mapped_column(String(255), comment="模型名称")
    description: Mapped[str | None] = mapped_column(String(255), comment="描述")


# 修正 model_creator 的引用
DictionaryPydantic = models.model_creator(Dictionary, exclude=("deleted_at",))
