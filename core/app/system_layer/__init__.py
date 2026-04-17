import core
from . import models
from . import route
from . import service
from . import source

from core import http
from .service import jwt, api
from .service.api import api_service


async def init():
    http.init_include_router(
        route.login.login_router.router,
        route.user.user_router.router,
        route.menu.menu_router.router,
        route.role.role_router.router,
        route.api.api_router.router,
    )
    http.register_router_middleware(
        api.CasbinAuthMiddleware,
        jwt.JWTMiddleware,
    )
    # 初始化系统数据（按依赖顺序：角色 -> 用户 -> 菜单 -> 接口 -> Casbin策略）
    await core.init_source(
        source.role_source,
        source.menu_source,
        source.user_source,
        source.casbin_source,
    )
    core.function_registration(api_service.init_api)
