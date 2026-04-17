from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base import models


class RoleAlreadyExistsError(Exception):
    def __init__(self, message="角色编码已存在"):
        self.message = message
        super().__init__(self.message)


class Role(models.Model):
    __tablename__ = "role"
    __table_args__ = {
        "comment": "角色管理"
    }

    name: Mapped[str | None] = mapped_column(String(255), comment="名称")
    code: Mapped[str | None] = mapped_column(String(255), comment="编码", unique=True)
    description: Mapped[str | None] = mapped_column(String(255), comment="描述")


RolePydantic = models.model_creator(Role, exclude=('deleted_at',))
