from core import base
from ..api import APIPydantic


class APISearch(base.PageInfo, APIPydantic, base.TimeInfo):
    pass
