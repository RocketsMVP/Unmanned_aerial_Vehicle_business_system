from sqlalchemy import select, func, update, delete, table, text

from core import base
from .casbin import casbin_service
from ..models import Role, request, RoleAlreadyExistsError, RolePydantic
from ..models.request import CasbinReq, CasbinAPI


class RoleService(base.Assembly):

    async def get_role_list(self, info: request.RoleSearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(Role)
            if info.name:
                db = db.where(Role.name.ilike(f'%{info.name}%'))
            if info.start_time:
                db = db.where(Role.created_at >= info.start_time)
            if info.end_time:
                db = db.where(Role.created_at <= info.end_time)
            count = await session.scalar(
                select(func.count()).select_from(Role).where(*db._where_criteria)
            )
            data = await session.scalars(
                db.limit(limit).offset(offset)
            )
        return data.all(), count

    async def get_role(self, id):
        async with self.get_db() as db:
            data = await db.scalars(select(Role).where(Role.id == id))
        return data.first()

    async def create_role(self, info: request.RolePydantic):
        async with self.get_db() as db:
            data = await db.scalars(
                select(Role).where(Role.code == info.code)
            )
            if data.first():
                raise RoleAlreadyExistsError
            role = Role(**info.model_dump(exclude_unset=True))
            db.add(role)
            await db.commit()
            await db.refresh(role)
        return role

    async def update_role(self, role: RolePydantic):
        async with self.get_db() as db:
            count = await db.scalar(
                select(func.count()).where(
                    Role.code == role.code,
                    Role.id != role.id  # 排除当前用户自身
                )
            )
            if count > 0:
                raise RoleAlreadyExistsError
            data = await db.scalars(
                select(Role).where(Role.id == role.id)
            )
            old_role = data.first()
            update_data = role.model_dump(exclude_unset=True, exclude={"id"})
            await db.execute(
                update(Role).where(Role.id == role.id).values(**update_data)
            )
            await casbin_service.update_casbin_role_mark(old_role.code, role.code)
            await db.commit()
        return

    async def delete_role(self, id):
        async with self.get_db() as db:
            await db.execute(
                delete(Role).where(Role.id == id)
            )
            await db.commit()
        return

    async def update_role_menu(self, cas: CasbinReq):
        await casbin_service.update_casbin(cas.code, cas.checked, 'menu')

    async def update_role_api(self, cas: CasbinAPI):
        await casbin_service.update_casbin(cas.code, cas.checked, 'api')

    async def get_role_permission(self, code: str):
        async with self.get_db() as session:
            data = await session.execute(
                text("SELECT v2 FROM casbin_rule WHERE v0 = :code AND v1 = 'menu'"),
                {"code": code}  # 参数化查询，防止 SQL 注入
            )
            menu = data.scalars().all()
            data = await session.execute(
                text("select v2 as path, v3 as act FROM casbin_rule where v0 = :code and v1 = 'api'"), {"code": code}
            )
            api = data.mappings().all()
            return {
                "menu": menu,
                "api": api
            }


role_service = RoleService()
