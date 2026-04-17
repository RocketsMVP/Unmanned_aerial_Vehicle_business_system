from . import models
from . import route
from . import service
from core import http


async def init():
    http.init_include_router(
        route.dictionary.dictionary_route.router,
    )
