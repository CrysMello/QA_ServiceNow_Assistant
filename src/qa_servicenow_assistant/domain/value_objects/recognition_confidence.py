"""Recognition confidence tiers (SAD 15.5 - Estrategia de Correspondencia)."""

from __future__ import annotations

from enum import Enum


class RecognitionConfidence(str, Enum):
    """SAD 15.5: correspondencia exata / parcial / baixa confianca / pagina
    desconhecida. Per SAD 15.5, LOW is explicitly "pagina considerada nao
    reconhecida" - only EXACT and PARTIAL count as recognized
    (see RecognitionResult.is_recognized)."""

    EXACT = "exact"
    PARTIAL = "partial"
    LOW = "low"
    UNKNOWN = "unknown"
