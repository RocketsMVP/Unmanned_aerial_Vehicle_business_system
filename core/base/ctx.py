import contextvars
from typing import Dict, Any

CTX: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "context", default={}
)
