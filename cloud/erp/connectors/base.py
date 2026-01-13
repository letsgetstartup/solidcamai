from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, List
from datetime import datetime

@dataclass(frozen=True)
class ErpEntitySpec:
    """
    Declares how to pull an ERP entity.
    The actual endpoint name can vary between ERP versions; keep configurable.
    """
    name: str                 # logical entity name used in SIMCO (e.g., "items")
    endpoint: str             # ERP endpoint path (e.g., "Items")
    primary_key_field: str    # e.g., "ItemCode" or "DocEntry"
    updated_at_field: Optional[str] = None  # e.g., "UpdateDate" or "UpdateDateTime"
    select: Optional[List[str]] = None      # fields to select (if supported)
    extra_filter: Optional[str] = None      # additional OData filter suffix

class ErpConnector(ABC):
    """
    Provider-agnostic ERP connector interface.
    """

    @abstractmethod
    async def healthcheck(self) -> Dict[str, Any]:
        """Check connection health."""
        ...

    @abstractmethod
    def list_entities(self) -> List[ErpEntitySpec]:
        """Return available/configured entities."""
        ...

    @abstractmethod
    async def fetch(
        self,
        entity: ErpEntitySpec,
        since: Optional[datetime],
        page_size: int = 200,
    ) -> Iterable[Dict[str, Any]]:
        """
        Yields ERP records as dicts.
        Must be safe to call repeatedly (idempotent fetch).
        """
        ...
