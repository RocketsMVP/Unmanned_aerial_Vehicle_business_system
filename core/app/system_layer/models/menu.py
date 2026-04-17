import enum

from sqlalchemy import String, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from core.base import models


class MenuClassify(str, enum.Enum):
    DIRECTORY = 'directory'
    MENU = "menu"


class MenuAlreadyExistsError(Exception):
    def __init__(self, message="编码已存在"):
        self.message = message
        super().__init__(self.message)


class Menu(models.Model):
    __tablename__ = "menu"
    __table_args__ = {"comment": "菜单管理"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), comment="名称")
    path: Mapped[str | None] = mapped_column(String(255), comment="路径")
    code: Mapped[str | None] = mapped_column(String(255), comment="编码")
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("menu.id"), comment="父菜单ID")

    icon: Mapped[str | None] = mapped_column(String(255), comment="图标")
    redirect: Mapped[str | None] = mapped_column(String(255), comment="重定向")
    active: Mapped[str | None] = mapped_column(String(255), comment="激活路径")
    component: Mapped[str | None] = mapped_column(String(255), comment="文件路径")
    link: Mapped[str | None] = mapped_column(String(255), comment="外链")
    is_hidden: Mapped[bool] = mapped_column(Boolean, comment="是否隐藏", default=False)
    is_keep_alive: Mapped[bool] = mapped_column(Boolean, comment="是否缓存", default=True)
    order: Mapped[int | None] = mapped_column(Integer, comment="排序", default=0)
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
    classify: Mapped[MenuClassify | None] = mapped_column(
        Enum(MenuClassify), nullable=True, comment="分类"
    )
    status: Mapped[bool] = mapped_column(Boolean, comment="状态", default=True)
    # 子菜单关系（一对多）
    children: Mapped[list["Menu"]] = relationship(
        "Menu",
        foreign_keys=[parent_id],  # 子菜单的外键字段
        lazy="immediate",  # 立即加载
        order_by=order.desc(),  # 排序
    )


MenuSavePydantic = models.model_creator(Menu, exclude=('deleted_at',))
MenuSavePydantic.model_rebuild(force=True)

MenuTreePydantic = models.model_creator_fields(Menu, exclude=(
    'path',
    'parent_id',
    'icon',
    'redirect',
    'active',
    'component',
    'link',
    'is_hidden',
    'is_keep_alive',
    'order',
    'remark',
    'classify',
    'status',
))
