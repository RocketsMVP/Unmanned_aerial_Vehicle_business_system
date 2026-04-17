import casbin_async_sqlalchemy_adapter
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class CasbinRule(casbin_async_sqlalchemy_adapter.CasbinRule):
    id: Mapped[int] = mapped_column(String(255), primary_key=True, use_existing_column=True)
    ptype: Mapped[str] = mapped_column(String(255), index=True, use_existing_column=True)
    v0: Mapped[str] = mapped_column(String(255), index=True, nullable=True, use_existing_column=True)
    v1: Mapped[str] = mapped_column(String(255), index=True, nullable=True, use_existing_column=True)
    v2: Mapped[str] = mapped_column(String(255), nullable=True, use_existing_column=True)
    v3: Mapped[str] = mapped_column(String(255), nullable=True, use_existing_column=True)
    v4: Mapped[str] = mapped_column(String(255), nullable=True, use_existing_column=True)
    v5: Mapped[str] = mapped_column(String(255), nullable=True, use_existing_column=True)


CasbinRule.__tablename__ = "casbin_rule"  # 表名（默认已为此值，可选修改）
CasbinRule.__table_args__ = {
    "comment": "权限策略",  # 自定义表注释（解决你的业务需求）
    "extend_existing": True  # 允许后续迁移时扩展表结构（如新增字段）
}
