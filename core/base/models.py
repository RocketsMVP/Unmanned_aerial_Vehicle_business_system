import hashlib
import sys
from typing import Optional, List, Tuple, Type, Container, Dict, Any, ForwardRef

from pydantic import BaseModel, create_model, Field
from sqlalchemy import func, Integer, select, Update, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, with_loader_criteria, Session, ColumnProperty, \
    RelationshipProperty, LoaderCriteriaOption
from core.base.assembly import Assembly

from datetime import datetime
from sqlalchemy import DateTime, event, inspect


# 设置默认查询过滤（排除已删除记录）
@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    if not execute_state.bind_mapper:
        return
    # 只对普通 SELECT / UPDATE 生效，且不是硬删除、也不是 column/relationship load
    if (
            (execute_state.is_select or execute_state.is_update)
            and not execute_state.is_column_load
            and not execute_state.is_relationship_load
            and not execute_state.session.info.get("hard_delete", False)
    ):
        entity = execute_state.bind_mapper.class_
        if hasattr(entity, "__table__") and "deleted_at" in entity.__table__.columns:
            stmt = execute_state.statement

            # 如果它不是一个 Select，就跳过
            if not isinstance(stmt, Select):
                return

            # 查一查 _with_options 里有没有 SoftDeleteMixin 的 LoaderCriteriaOption
            already = False
            for opt in getattr(stmt, "_with_options", ()):
                if isinstance(opt, LoaderCriteriaOption):
                    # LoaderCriteriaOption.target_entity 在 SQLAlchemy 2.0；1.4 下可能是 ._target
                    target = getattr(opt, "target_entity", None) or getattr(opt, "_target", None)
                    if target is Model:
                        already = True
                        break

            if not already:
                if "SELECT count(*)" in str(stmt):
                    execute_state.statement = stmt.where(entity.deleted_at.is_(None))
                    return
                execute_state.statement = stmt.options(
                    with_loader_criteria(
                        Model,
                        lambda cls: cls.deleted_at.is_(None),
                        include_aliases=True,
                    )
                )


# do_orm_execute 事件监听器
@event.listens_for(Session, "do_orm_execute")
def intercept_delete(orm_execute_state):
    if not orm_execute_state.bind_mapper:
        return
    # 检查是否为删除操作
    if orm_execute_state.is_delete:
        # 获取语句的目标实体
        entity = orm_execute_state.bind_mapper.class_
        if hasattr(entity, "__table__") and "deleted_at" in entity.__table__.columns:
            # 检查实体是否支持软删除（继承自 SoftDeleteMixin）
            if entity and issubclass(entity, Model):
                # 检查是否要求硬删除
                hard_delete = orm_execute_state.session.info.get("hard_delete", False)
                if not hard_delete:
                    # 将删除语句替换为更新语句
                    orm_execute_state.statement = (
                        Update(entity)
                        .values(deleted_at=datetime.now())
                        .where(
                            1 == 1 if orm_execute_state.statement.whereclause is None else orm_execute_state.statement.whereclause))


class Model(DeclarativeBase, Assembly):
    """
    通用模型基类，支持软删除（deleted_at 字段）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, sort_order=-100, comment="主键 ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), nullable=False, sort_order=-99,
                                                 comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), insert_default=func.now(),
                                                 nullable=False, sort_order=-98, comment="更新时间")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="删除时间",
                                                        sort_order=-97, index=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.id}>"


def serialize_datetime(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


orm_config = {
    "json_encoders": {
        datetime: serialize_datetime
    },
    "from_attributes": True,
    "arbitrary_types_allowed": True,
    "validate_by_name": True,
}

# 全局缓存，用于存储已生成的 Pydantic 模型
_model_cache: Dict[str, Type[BaseModel]] = {}
# 跟踪正在处理的模型，防止循环引用导致的无限递归
_processing_models: set[str] = set()


def generate_cache_key(
        db_model: Type,
        exclude: Container[str],
        optional: Container[str],
        forced: bool
) -> str:
    """生成唯一的缓存键，基于模型和配置参数"""
    exclude_str = ":".join(sorted(exclude))
    optional_str = ":".join(sorted(optional))
    key_str = f"{db_model.__name__}:{exclude_str}:{optional_str}:{forced}"
    return hashlib.md5(key_str.encode()).hexdigest()


def sqlalchemy_to_pydantic(
        db_model: Type,
        *,
        config,
        exclude: Container[str] = [],
        optional: Container[str] = [],
        forced: bool = False
) -> Type[BaseModel]:
    # 生成缓存键
    cache_key = generate_cache_key(db_model, exclude, optional, forced)

    # 检查缓存中是否已有该模型
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    # 检查是否正在处理该模型（防止循环引用）
    if cache_key in _processing_models:
        # 返回 ForwardRef，延迟解析
        return ForwardRef(f"{db_model.__name__}_{cache_key[:8]}MdPydantic")

    # 标记当前模型为正在处理
    _processing_models.add(cache_key)

    try:
        mapper = inspect(db_model)
        fields = {}
        for attr in mapper.attrs:
            name = attr.key
            if name in exclude:
                continue
            python_type: Optional[type] = None
            default = None
            description = ""

            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    column = attr.columns[0]
                    description = column.comment
                    if hasattr(column.type, "impl"):
                        if hasattr(column.type.impl, "python_type"):
                            python_type = column.type.impl.python_type
                    elif hasattr(column.type, "python_type"):
                        python_type = column.type.python_type
                    assert python_type, f"Could not infer python_type for column {column}"

                    # JSON 列使用 Any 类型，支持 list 和 dict
                    if hasattr(column.type, 'python_type') and column.type.python_type == dict:
                        # 检查是否是 JSON 类型
                        from sqlalchemy import JSON
                        if isinstance(column.type, JSON):
                            python_type = Any  # JSON 列可以是任意类型

                    if column.name in optional:
                        python_type = Optional[python_type]
                    elif column.default is None and not column.nullable:
                        default = ...

            elif isinstance(attr, RelationshipProperty):
                related_model = attr.entity.class_
                is_self_reference = related_model == db_model
                related_cache_key = generate_cache_key(related_model, exclude, optional, forced)
                if is_self_reference or related_cache_key in _processing_models:
                    # 自引用或循环引用，使用 ForwardRef
                    related_model_name = f"{related_model.__name__}_{related_cache_key[:8]}MdPydantic"
                    if attr.uselist:
                        python_type = Optional[List[ForwardRef(related_model_name)]]
                        default = []
                    else:
                        python_type = Optional[ForwardRef(related_model_name)]
                        default = None
                    if name in optional:
                        python_type = Optional[python_type]
                        default = None
                else:
                    # 非自引用且非循环引用，递归生成相关模型
                    if not forced:
                        rela_fields = [x for x in inspect(related_model).column_attrs.keys() + inspect(
                            related_model).relationships.keys() if x not in ['id', 'name']]
                    else:
                        rela_fields = inspect(related_model).column_attrs.keys()
                    rela = sqlalchemy_to_pydantic(related_model, exclude=rela_fields, config=config, optional=optional,
                                                  forced=forced)
                    if attr.uselist:
                        python_type = Optional[List[rela]]
                        default = []
                    else:
                        python_type = Optional[rela]
                        default = None

            if python_type:
                fields[name] = (python_type, Field(default=default, description=description))

        # 创建 Pydantic 模型
        model_name = f"{db_model.__name__}_{cache_key[:8]}MdPydantic"
        pydantic_model = create_model(model_name, __config__=config, **fields)

        # 将生成的模型注册到全局命名空间
        sys.modules[__name__].__dict__[model_name] = pydantic_model

        # 将生成的模型存入缓存
        _model_cache[cache_key] = pydantic_model

        return pydantic_model

    finally:
        # 完成后移除正在处理的标记
        _processing_models.remove(cache_key)


# 手动解析 ForwardRef
def resolve_forward_refs():
    for model in _model_cache.values():
        model.model_rebuild()


def model_creator(model: Type[Model], exclude: Tuple[str, ...] = (), forced=False):
    pydantic_model = sqlalchemy_to_pydantic(
        model,
        exclude=exclude,
        config=orm_config,  # 确保 orm_config 已定义
        optional=inspect(model).column_attrs.keys() + inspect(model).relationships.keys(),
        forced=forced
    )
    resolve_forward_refs()  # 解析所有 ForwardRef
    return pydantic_model


def model_creator_fields(model: Type[Model], exclude: Tuple[str, ...] = ()):
    # 默认排除 id, created_at, updated_at, deleted_at
    base_exclude = ("id", "created_at", "updated_at", "deleted_at") + exclude
    pydantic_model = sqlalchemy_to_pydantic(model, exclude=base_exclude, config=orm_config,
                                            optional=inspect(model).column_attrs.keys() + inspect(
                                                model).relationships.keys(), forced=False)
    resolve_forward_refs()
    return pydantic_model


# 其他部分如 TimeInfo、PageInfo、Response 等保持不变
class BaseModel(BaseModel):
    pass


BaseModel.model_config = orm_config


class PageInfo(BaseModel):
    page: Optional[int] = Field(1, description="页码,默认为 1")
    page_size: Optional[int] = Field(10, description="每页数量，默认为 10")


class GetById(BaseModel):
    id: int = Field(..., description="主键ID")


class TimeInfo(BaseModel):
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class IdsReq(BaseModel):
    ids: List[int] = Field(..., description="主键ID列表")


class Response(BaseModel):
    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="返回信息")
    data: Optional[Dict[str, Any]] | str = Field(None, description="返回数据")

class ListResponse(BaseModel):
    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="返回信息")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="返回数据")
