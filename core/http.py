import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Type

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, select
from starlette.middleware.gzip import GZipMiddleware

from core.intra import config

from core import module, db

# 存储待注册的中间件
_pending_middlewares: List[Type] = []

fus = []


def function_registration(*fu):
    """注册函数到全局列表"""
    fus.extend(fu)


async def execution_func():
    """执行所有已注册的函数"""
    for func in fus:
        if inspect.iscoroutinefunction(func):
            await func()
        else:
            func()


def register_router_middleware(*handler):
    """注册中间件（延迟到应用启动前执行）"""
    for i in handler:
        app.add_middleware(i)


_rq_process = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    """应用生命周期管理（替代 @app.on_event）"""

    # === Startup ===
    # 检查是否需要初始化数据库（每个 worker 进程独立初始化）
    if db.async_engine is None:
        await db.init_database()

    # 验证数据库连接
    try:
        async with db.async_engine.connect() as conn:
            await conn.scalar(select(1))
    except RuntimeError as e:
        logging.error(e)
        if "TCPTransport closed" in str(e):
            await asyncio.sleep(0.1 * (2 ** 3))

    # 执行注册函数
    await execution_func()

    yield

    # === Shutdown ===
    if db.async_engine:
        await db.async_engine.dispose()


# 使用 lifespan 参数创建 FastAPI 应用
app = FastAPI(
    lifespan=lifespan,
    routes=[],
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("system.cors"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


@app.get("/ping")
async def ping():
    return {"message": "pong"}


async def run():
    """运行前的初始化（必须在应用启动前调用）"""
    # 先初始化数据库（必须在模块初始化之前）
    if db.async_engine is None:
        await db.init_database()

    # 验证数据库连接
    try:
        async with db.async_engine.connect() as conn:
            await conn.scalar(select(1))
    except RuntimeError as e:
        logging.error(e)
        if "TCPTransport closed" in str(e):
            await asyncio.sleep(0.1 * (2 ** 3))

    # 再初始化模块和中间件
    await module.initialize_module()


def init_include_router(*routes: APIRouter):
    """注册路由"""
    for i in routes:
        app.include_router(i)
