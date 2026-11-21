"""Uma despesa lida de uma fatura de cartão, ainda sem gravar."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LancamentoFatura:
    data: date
    descricao: str
    valor_centavos: int
    numero_parcela: int
    total_parcelas: int
