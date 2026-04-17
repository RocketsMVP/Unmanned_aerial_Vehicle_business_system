from typing import List

from sqlalchemy import select, func, delete, update, table, text
from core import base
from ..models.dictionary import Dictionary, DictionaryPydantic, DictionaryAlreadyExistsError
from ..models.request import DictionarySearch


class DictionaryService(base.Assembly):

    async def get_dictionary_list(self, info: DictionarySearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(Dictionary)
            if info.name:
                db = db.where(Dictionary.name.like(f"%{info.name}%"))
            count = await session.scalar(
                select(func.count()).select_from(Dictionary).where(*db._where_criteria)
            )
            data = await session.scalars(db.limit(limit).offset(offset))
        return data.all(), count

    async def get_dictionary_select(self, code: List[str]):
        result = {}
        for i in code:
            async with self.get_db() as db:
                data = await db.scalar(select(Dictionary).where(Dictionary.code == i))
                mold = data.mold
                if mold == "select":
                    res = data.dictionary_json
                elif mold == "model":
                    data = await db.execute(
                        text(f"""
                                SELECT id, name, deleted_at
                                FROM {data.model_name}
                                WHERE deleted_at IS NULL
                                ORDER BY id DESC
                            """)
                    )
                    res = data.mappings().all()
                result[i] = {
                    "type": mold,
                    "data": res,
                }
        return result

    async def get_dictionary(self, id: int):
        async with self.get_db() as db:
            data = await db.scalar(select(Dictionary).where(Dictionary.id == id))
        return data

    async def create_dictionary(self, info: DictionaryPydantic):
        async with self.get_db() as db:
            data = await db.scalars(
                select(Dictionary).where(Dictionary.code == info.code)
            )
            if data.first():
                raise DictionaryAlreadyExistsError
            new_dict = Dictionary(**info.model_dump(exclude_unset=True))
            db.add(new_dict)
            await db.commit()
            await db.refresh(new_dict)
        return new_dict

    async def update_dictionary(self, info: DictionaryPydantic):
        async with self.get_db() as db:
            await db.execute(
                update(Dictionary).where(Dictionary.id == info.id).values(
                    **info.model_dump(exclude_unset=True, exclude={"id", "deleted_at"}))
            )
            await db.commit()
        return

    async def delete_dictionary(self, id: int):
        async with self.get_db() as db:
            await db.execute(delete(Dictionary).where(Dictionary.id == id))
            await db.commit()
        return


dictionary_service = DictionaryService()
