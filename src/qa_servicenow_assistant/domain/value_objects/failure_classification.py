"""Failure classification tiers (SAD 19.2, 19.6)."""

from __future__ import annotations

from enum import Enum


class FailureClassification(str, Enum):
    """SAD 19.6: falhas transitorias (timeout de carregamento, elemento
    temporariamente indisponivel, perda momentanea de conectividade,
    falha temporaria do navegador) sao elegiveis para retry; falhas
    permanentes (elemento inexistente na Base de Conhecimento, erro de
    regra de negocio) nao sao."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
