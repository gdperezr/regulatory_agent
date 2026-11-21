"""Total de uma fatura em um mês, agrupado por cartão."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumoFatura:
    mes_fatura: str
    cartao: str
    valor_centavos: int

    @classmethod
    def da_linha(cls, linha) -> "ResumoFatura":
        return cls(
            mes_fatura=linha["invoice_month"],
            cartao=linha["card"],
            valor_centavos=linha["amount_cents"],
        )
