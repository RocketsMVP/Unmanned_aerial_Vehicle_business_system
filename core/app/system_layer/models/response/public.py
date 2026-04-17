from typing import Dict, Any, List

from core import base


class PublicResponse(base.Response):
    data: List[Dict[str, Any]]
