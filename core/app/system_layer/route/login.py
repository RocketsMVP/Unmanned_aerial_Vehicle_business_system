import base64
import random
import string

from captcha.image import ImageCaptcha
from fastapi import APIRouter

from core import config, cache, base
from ..models import AccountNotFoundError, PasswordIncorrectError
from ..models.request.user import LoginReq
from ..service.user import user_service


class LoginRouter(base.Assembly):

    def __init__(self):
        self.router = APIRouter(prefix="/base", tags=["基础"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/captcha",
            summary="获取图形验证码",
            response_model=base.Response
        )
        async def get_captcha():
            # 获取配置
            try:
                driver_cfg = {
                    "img-height": config.get_int('captcha.img-height'),
                    "img-width": config.get_int('captcha.img-width'),
                    "key-long": config.get_int('captcha.key-long')
                }

                # 创建验证码驱动
                image = ImageCaptcha(width=driver_cfg["img-width"], height=driver_cfg["img-height"])

                # 生成随机验证码
                captcha_text = ''.join(random.choices(string.digits, k=driver_cfg["key-long"]))

                # 生成验证码图片
                captcha_image = image.generate(captcha_text)

                # 将图片转换为 base64 编码
                captcha_image.seek(0)
                b64s = base64.b64encode(captcha_image.read()).decode('utf-8')

                # 生成唯一的验证码 ID
                captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

                # 模拟缓存存储，这里可以根据实际需求替换为 Redis 等缓存系统
                await cache.set(captcha_id, captcha_text)

                return self.success_correctly_data({
                    "captcha_id": captcha_id,
                    "pic_path": f"data:image/png;base64,{b64s}",
                    "captcha_length": driver_cfg["key-long"]
                }, "验证码获取成功")
            except Exception as e:
                self.S().error(e)
                return self.fail_correctly("验证码获取失败")

        @self.router.post(
            "/login",
            summary="用户登录",
            response_model=base.Response
        )
        async def login(login: LoginReq):
            if await cache.verify(login.captcha_id, login.captcha):
                try:
                    data = await user_service.login(login.login, login.password)
                    return self.success_correctly_data(data, "登录成功")
                except AccountNotFoundError as e:
                    return self.fail_correctly(e.message)
                except PasswordIncorrectError as e:
                    return self.fail_correctly(e.message)
                except Exception as e:
                    self.S().error(e)
                    return self.fail_correctly("登录失败")
            else:
                return self.fail_correctly("验证码错误")


login_router = LoginRouter()
