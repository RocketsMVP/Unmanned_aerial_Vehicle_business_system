from sqlalchemy import select, func, update, delete, text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from core import base
from .casbin import casbin_service
from .jwt import EXCLUDED_ROUTES
from ..models import API, request
from core.http import app
from fastapi import Request, Response


class APIService(base.Assembly):

    async def get_api_list(self, info: request.APISearch):
        limit = info.page_size
        offset = limit * (info.page - 1)
        async with self.get_db() as session:
            db = select(API)
            if info.name:
                db = db.where(API.name.ilike(f'%{info.name}%'))
            if info.start_time:
                db = db.where(API.created_at >= info.start_time)
            if info.end_time:
                db = db.where(API.created_at <= info.end_time)
            count = await session.scalar(
                select(func.count()).select_from(API).where(*db._where_criteria)
            )
            data = await session.scalars(
                db.limit(limit).offset(offset)
            )
        return data.all(), count

    async def get_api(self, id):
        async with self.get_db() as db:
            data = await db.scalars(select(API).where(API.id == id))
        return data.first()

    async def init_api(self):
        api_list = []
        for route in app.routes:
            if hasattr(route, "tags") and route.tags != ['基础'] and route.path != '/ping':
                api_list.append(
                    API(
                        name=route.summary,
                        path=route.path,
                        method=str(route.methods).strip("{''}"),
                        group=route.tags[0]
                    )
                )
        async with self.get_db(hard_delete=True) as db:
            await db.execute(text("TRUNCATE TABLE api"))
            db.add_all(api_list)
            await db.commit()


api_service = APIService()

"""
API 权限校验中间件
"""


class CasbinAuthMiddleware(BaseHTTPMiddleware, base.Assembly):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # 公开接口不做权限校验
        for prefix in EXCLUDED_ROUTES:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        # 从请求中获取用户身份（需根据实际认证方式调整，如 JWT 解析）
        user = self.with_value("user")
        role = user['role']
        path = request.url.path  # 当前请求路径
        method = request.method.upper()  # 请求方法（GET/POST 等）

        # 校验权限
        enforcer = await casbin_service.get_enforcer()
        has_permission = enforcer.enforce(role, 'api', path, method)
        if not has_permission and role != 'admin':
            # 认证通过但权限不足
            return JSONResponse(
                status_code=200,
                content={
                    "code": 401,
                    "msg": "无权限访问，请联系管理员"
                }
            )
        # 允许访问，继续处理请求
        return await call_next(request)
