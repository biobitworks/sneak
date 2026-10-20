"""Sneak local contracts: custody evidence, connectors, score gate, LOMO."""

__version__ = "0.1.0"

from .contracts import EvidenceRef, Verdict
from .connectors import ConnectorRuntime, ConnectorStatus

__all__ = [
    "EvidenceRef",
    "Verdict",
    "ConnectorRuntime",
    "ConnectorStatus",
    "__version__",
]
