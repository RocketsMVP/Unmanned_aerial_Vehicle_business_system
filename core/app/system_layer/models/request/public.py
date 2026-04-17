from typing import Optional

from core import base


class MenuSearch(base.PageInfo):
    page_size: Optional[int] = 0
    model: str
