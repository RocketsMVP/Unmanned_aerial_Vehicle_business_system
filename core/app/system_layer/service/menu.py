from sqlalchemy import select, func, update, delete

from core import base
from ..models import Menu, request, MenuAlreadyExistsError, MenuSavePydantic


class MenuService(base.Assembly):

    async def get_menu_list(self, info: request.MenuSearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(Menu)
            db = db.where(Menu.parent_id.is_(None))
            if info.name:
                db = db.where(Menu.name.ilike(f'%{info.name}%'))
            if info.start_time:
                db = db.where(Menu.created_at >= info.start_time)
            if info.end_time:
                db = db.where(Menu.created_at <= info.end_time)
            count = await session.scalar(
                select(func.count()).select_from(Menu).where(*db._where_criteria)
            )
            data = await session.scalars(
                db.limit(limit).offset(offset).order_by(Menu.order.desc())
            )
        return data.all(), count

    async def get_menu(self, id):
        async with self.get_db() as db:
            data = await db.scalars(select(Menu).where(Menu.id == id))
        return data.first()

    async def get_tree_menu(self):
        async with self.get_db() as db:
            data = await db.scalars(
                select(Menu).where(Menu.parent_id.is_(None)).order_by(Menu.order.desc())
            )
        return data.all()

    async def create_menu(self, info: request.MenuSavePydantic):
        async with self.get_db() as db:
            data = await db.scalars(
                select(Menu).where(Menu.code == info.code)
            )
            if data.first():
                raise MenuAlreadyExistsError
            menu = Menu(**info.model_dump(exclude_unset=True, exclude={"id", "children"}))
            db.add(menu)
            await db.commit()
            await db.refresh(menu)
        return menu

    async def update_menu(self, menu: MenuSavePydantic):
        async with self.get_db() as db:
            count = await db.scalar(
                select(func.count()).where(
                    Menu.code == menu.code,
                    Menu.id != menu.id  # 排除当前用户自身
                )
            )
            if count > 0:
                raise MenuAlreadyExistsError

            update_data = menu.model_dump(exclude_unset=True, exclude={"id", "children"})
            await db.execute(
                update(Menu).where(Menu.id == menu.id).values(**update_data)
            )
            await db.commit()
        return

    async def delete_menu(self, id):
        async with self.get_db() as db:
            await db.execute(
                delete(Menu).where(Menu.id == id)
            )
            await db.commit()
        return


menu_service = MenuService()
