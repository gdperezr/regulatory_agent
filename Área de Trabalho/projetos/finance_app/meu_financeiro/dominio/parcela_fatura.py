"""Uma parcela de compra dentro do mês de fechamento da fatura."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParcelaFatura:
    """Parcela já distribuída: número, mês da fatura e valor em centavos."""

    numero: int
    mes_fatura: str
    valor_centavos: int


@dataclass(frozen=True)
class ParcelaGravada:
    """Parcela que já está no banco, com o id da linha."""

    id: int
    numero: int
    mes_fatura: str
    valor_centavos: int
