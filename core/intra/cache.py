"""缓存管理模块。

基于 Redis 的异步缓存服务，使用 redis-py 实现。
"""

from datetime import timedelta
import logging
from typing import Any

import redis.asyncio as aioredis

from core.intra import viper

# 默认过期时间（10 分钟）
DEFAULT_TTL = int(timedelta(minutes=10).total_seconds())


def _get_redis_config() -> dict | None:
    """获取 Redis 配置。

    Returns:
        Redis 配置字典或 None
    """
    return viper.config.get("redis")


# 初始化连接池
redis_config = _get_redis_config()

if redis_config:
    _async_pool = aioredis.ConnectionPool(
        host=redis_config.get("host", "localhost"),
        port=redis_config.get("port", 6379),
        db=redis_config.get("db", 0),
        password=redis_config.get("password"),
        decode_responses=True,
    )
    logging.info("Redis 异步连接池初始化成功")
else:
    _async_pool = None
    logging.warning("Redis 配置未找到，缓存服务将不可用")


class CacheManager:
    """基于 Redis 的异步缓存管理器。"""

    async def _get_client(self) -> aioredis.Redis | None:
        """获取 Redis 异步客户端。"""
        if _async_pool:
            return aioredis.Redis(connection_pool=_async_pool)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """设置缓存项。

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 可选的过期时间（秒），覆盖默认 TTL
        """
        client = await self._get_client()
        if not client:
            return
        expire = ttl or DEFAULT_TTL
        await client.set(key, value, ex=expire)
        logging.debug(f"Set cache key: {key}")

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存项。

        Args:
            key: 缓存键
            default: 默认值（当缓存不存在或过期时返回）

        Returns:
            缓存值或默认值
        """
        client = await self._get_client()
        if not client:
            return default
        result = await client.get(key)
        if result is None:
            logging.debug(f"Cache miss for key: {key}")
            return default
        return result

    async def delete(self, key: str) -> None:
        """删除缓存项。

        Args:
            key: 缓存键
        """
        client = await self._get_client()
        if not client:
            return
        await client.delete(key)
        logging.debug(f"Deleted cache key: {key}")

    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在。

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        client = await self._get_client()
        if not client:
            return False
        return await client.exists(key) > 0

    async def clear(self) -> None:
        """清空所有缓存。"""
        client = await self._get_client()
        if client:
            await client.flushdb()
            logging.info("Cache cleared")

    async def set_per(self, key: str, value: Any, ttl: int) -> None:
        """使用指定过期时间设置缓存项。

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        await self.set(key, value, ttl=ttl)

    async def verify(self, key: str, expected: Any, clear: bool = True) -> bool:
        """验证缓存值是否与期望值匹配。

        Args:
            key: 缓存键
            expected: 期望的值
            clear: 验证后是否清除缓存

        Returns:
            是否匹配
        """
        actual = await self.get(key)
        if clear:
            await self.delete(key)
        return actual == expected


# 全局缓存管理器实例
cache = CacheManager()
