import uuid

from sqlalchemy import select, func, update, delete, text
from sqlalchemy.orm import joinedload, with_loader_criteria

from core import base
from . import jwt
from ..models import User, AccountNotFoundError, PasswordIncorrectError, request, UserAlreadyExistsError, \
    UserUpdatePydantic, Role, Menu


class UserService(base.Assembly):

    async def login(self, login, password):
        async with self.get_db() as db:
            data = await db.scalars(
                select(User).where(User.login == login)
            )
            res = data.first()
        if res:
            if res.password == self.md5v(password.encode()):
                token = jwt.create_token({
                    'login': login,
                    'uuid': str(res.uuid),
                    'id': str(res.id),
                    'name': res.name,
                    'role': str(res.role.code),
                })
                return token
            else:
                raise PasswordIncorrectError
        else:
            raise AccountNotFoundError

    async def get_user_list(self, info: request.UserSearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(User)
            # 3. 动态拼接 WHERE
            if info.name:
                # SQLAlchemy 的 contains 对应 LIKE '%value%'
                db = db.where(User.name.contains(info.name))
            if info.login:
                db = db.where(User.login.contains(info.login))
            if info.start_time:
                db = db.where(User.created_at >= info.start_time)
            if info.end_time:
                db = db.where(User.created_at <= info.end_time)
            count = await session.scalar(
                select(func.count()).select_from(User).where(*db._where_criteria)
            )
            data = await session.scalars(
                db.limit(limit).offset(offset)
            )
        return data.all(), count

    async def get_user(self, id):
        async with self.get_db() as db:
            data = await db.scalars(
                select(User).where(User.id == id)
            )
        return data.first()

    async def according_token_obtain(self, code):
        async with self.get_db() as db:
            data = await db.execute(
                text("SELECT v2 FROM casbin_rule WHERE v0 = :code AND v1 = 'menu'"),
                {"code": code}  # 参数化查询，防止 SQL 注入
            )
            menu = data.scalars().all()
            data = await db.scalars(
                select(Menu).where(Menu.parent_id.is_(None)).options(
                    with_loader_criteria(
                        Menu,
                        Menu.code.in_(menu)
                    )
                ))
        return data.all()

    async def create_user(self, info: request.UserPydantic):
        user = User(**info.model_dump(exclude_unset=True, exclude={"role"}))
        async with self.get_db() as db:
            data = await db.scalars(
                select(User).where(User.login == user.login)
            )
            if data.first():
                raise UserAlreadyExistsError
            if not user.password:
                user.password = self.md5v(self.get_viper().get('system.default-password').encode('utf-8'))
            else:
                user.password = self.md5v(user.password.encode('utf-8'))
            user.uuid = uuid.uuid4()
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    async def update_user(self, user: UserUpdatePydantic):
        async with self.get_db() as db:
            count = await db.scalar(
                select(func.count()).where(
                    User.login == user.login,
                    User.id != user.id  # 排除当前用户自身
                )
            )
            if count > 0:
                raise UserAlreadyExistsError

            update_data = user.model_dump(exclude_unset=True, exclude={"id", "role"})
            await db.execute(
                update(User).where(User.id == user.id).values(**update_data)
            )
            await db.commit()
        return

    async def delete_user(self, id):
        async with self.get_db() as db:
            await db.execute(
                delete(User).where(User.id == id)
            )
            await db.commit()
        return


user_service = UserService()
