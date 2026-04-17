import asyncio
import logging

import jwt
from fastapi import Request
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware

import core.base
from core import config
from core.base import customization_correctly, Assembly


# 读取配置文件

# 单例飞行组模拟
class SingleFlight:
    def __init__(self):
        self.lock = asyncio.Lock()  # 改为异步锁
        self.in_flight = {}

    async def do(self, key, func):  # 方法改为异步
        async with self.lock:  # 使用 async with
            if key in self.in_flight:
                return self.in_flight[key]
            future = asyncio.Future()  # 使用 asyncio.Future
            self.in_flight[key] = future
        try:
            result = func()  # 等待 func 执行（func 需为异步）
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            async with self.lock:  # 使用 async with
                del self.in_flight[key]
        return future.result()


single_flight = SingleFlight()  # 实例化

EXCLUDED_ROUTES = [
    "/base",
    '/docs',
    '/redoc',
    '/openapi.json',
    '/ping',
    '/agent/chat/share',  # 分享接口免登录
    '/agent/chat/conversation',  # 对话管理免登录
]


# 基础声明模型
# JWTMiddleware jwt 自定义中间件
class JWTMiddleware(BaseHTTPMiddleware, Assembly):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        for prefix in EXCLUDED_ROUTES:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        return await self.jwt_middleware(request, call_next)

    async def jwt_middleware(self, request: Request, call_next):
        token = request.headers.get(config.get('jwt.token-prefix'))
        if not token:
            return customization_correctly(403, None, "访问令牌缺失!")
        try:
            claims = self.get_claims(token)
            if claims['exp'] - datetime.now().timestamp() < claims['buffer_time']:
                claims['exp'] = datetime.now() + timedelta(seconds=config.get_int('jwt.expires-time'))
                ntwoken = await self.new_token(token, claims)
                response = customization_correctly(402, None, "访问令牌已过期!")
                response.headers["new-token"] = ntwoken
                response.headers["new-expires-at"] = claims['exp'].strftime('%Y-%m-%d %H:%M:%S')
                return response
            self.with_context('uid', claims['id'])
            self.with_context('user', claims)
        except jwt.ExpiredSignatureError as e:
            logging.error(e)
            return customization_correctly(403, None, "访问令牌已过期，请重新登录!")
        except jwt.InvalidTokenError as e:
            logging.error(e)
            return customization_correctly(403, None, "访问令牌令牌无效!")
        except Exception as e:
            logging.error(e)
            return customization_correctly(403, None, "访问令牌已过期，请重新登录!")
        return await call_next(request)

    # ErrorChecking 错误校验
    def error_checking(self, status_code, message):
        return core.base.write_information(status_code, None, message)

    # NewToken 创建一个token
    async def new_token(self, old_token, claims):
        key = f"{config.get('jwt.jwt-prefix')}:{old_token}"
        v = await single_flight.do(key, lambda: create_token(claims))
        return v

    # GetClaims 获取claims
    def get_claims(self, token_string):
        try:
            claims = jwt.decode(token_string, config.get('jwt.signing-key'), algorithms=["HS256"])
            return claims
        except jwt.PyJWTError as err:
            raise err


def create_token(claims):
    iat = datetime.utcnow()  # 签发时间（当前时间）需要 UTC 时间，校验的时候默认 UTC 时间

    jwt_cfg = {
        "issuer": config.get('jwt.issuer'),
        "buffer_time": config.get_int('jwt.buffer-time'),
        "iat": iat,
        "nbf": iat - timedelta(seconds=1000),
        "exp": iat + timedelta(seconds=config.get_float("jwt.expires-time"))
    }
    claims.update(jwt_cfg)
    token = jwt.encode(claims, config.get('jwt.signing-key'), algorithm="HS256")
    return token
