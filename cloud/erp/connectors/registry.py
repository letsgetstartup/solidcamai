from __future__ import annotations

from typing import Dict, Type
from .base import ErpConnector

_CONNECTORS: Dict[str, Type[ErpConnector]] = {}

def register(provider: str):
    def _decorator(cls: Type[ErpConnector]):
        _CONNECTORS[provider] = cls
        return cls
    return _decorator

def get_connector_class(provider: str) -> Type[ErpConnector]:
    if provider not in _CONNECTORS:
        raise ValueError(f"Unsupported ERP provider: {provider}. Registered: {list(_CONNECTORS.keys())}")
    return _CONNECTORS[provider]
