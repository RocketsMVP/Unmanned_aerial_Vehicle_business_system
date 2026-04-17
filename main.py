# -*- coding: utf-8 -*-
import asyncio
import importlib.util
import multiprocessing
import sys

import uvicorn

from core import config, http


def _is_windows() -> bool:
    """判断是否为 Windows 系统"""
    return sys.platform == "win32"


def number_of_workers():
    """计算推荐的 worker 数量，Windows 下固定为 1"""
    if _is_windows():
        # Windows 上 multiprocessing + uvloop 不稳定，固定单 worker
        return 1
    return (multiprocessing.cpu_count() * 2) + 1


def _get_event_loop():
    """获取事件循环类型"""
    if _is_windows():
        return "asyncio"
    if importlib.util.find_spec("uvloop") is not None:
        return "uvloop"
    return "asyncio"


async def main_runner():
    await http.run()

    loop_type = _get_event_loop()
    workers = config.get_int("system.workers") or number_of_workers()

    server_config = uvicorn.Config(
        "core.http:app",
        host=config.get("system.host"),
        port=config.get_int("system.port"),
        loop=loop_type,
        workers=workers,
    )
    server = uvicorn.Server(config=server_config)
    await server.serve()


if __name__ == "__main__":
    if _is_windows():
        asyncio.run(main_runner())
    else:
        try:
            uvloop = importlib.import_module("uvloop")
            uvloop.run(main_runner())
        except (ImportError, OSError):
            # uvloop 不可用或启动失败，降级到标准 asyncio
            asyncio.run(main_runner())

