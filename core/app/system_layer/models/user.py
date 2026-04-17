import uuid

from sqlalchemy import Column, UUID, String, Integer, ForeignKey, JSON, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .role import Role
from core.base import models


class AccountNotFoundError(Exception):
    def __init__(self, message="账号不存在"):
        self.message = message
        super().__init__(self.message)


class PasswordIncorrectError(Exception):
    def __init__(self, message="密码错误"):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(Exception):

    def __init__(self, message="账号已存在"):
        self.message = message
        super().__init__(self.message)


class User(models.Model):
    __tablename__ = "user"
    __table_args__ = {
        "comment": "用户管理",
    }

    uuid: Mapped[str] = mapped_column(CHAR(36), default=uuid.uuid4, comment='用户唯一标识')
    name: Mapped[str] = mapped_column(String(255), comment="名称")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像")
    login: Mapped[str] = mapped_column(String(255), nullable=False, comment="登录名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码")
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("role.id"), comment="角色ID")
    role: Mapped["Role"] = relationship(
        "Role",
        foreign_keys=[role_id],
        lazy="immediate",
    )
    sex: Mapped[str | None] = mapped_column(String(255), comment="性别")
    state: Mapped[int | None] = mapped_column(Integer, comment="状态")
    layout: Mapped[dict[str, any] | None] = mapped_column(JSON, comment="布局")


UserPydantic = models.model_creator(User, exclude=('password', 'deleted_at', 'uuid'))
UserAllPydantic = models.model_creator_fields(User)
UserUpdatePydantic = models.model_creator(User, exclude=("created_at", "updated_at", "deleted_at", "password", "uuid"))
UserTokenPydantic = models.model_creator_fields(User, exclude=('password', 'deleted_at', 'uuid'))
