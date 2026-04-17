from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.base import models


class API(models.Model):
    __tablename__ = "api"
    __table_args__ = {
        "comment": "路由管理"
    }
    name: Mapped[str | None] = mapped_column(String(255), comment="名称")
    path: Mapped[str | None] = mapped_column(String(255), comment="路径")
    method: Mapped[str | None] = mapped_column(String(255), comment="方法")
    group: Mapped[str | None] = mapped_column(String(255), comment="分组")


APIPydantic = models.model_creator(API, exclude=("deleted_at",))
