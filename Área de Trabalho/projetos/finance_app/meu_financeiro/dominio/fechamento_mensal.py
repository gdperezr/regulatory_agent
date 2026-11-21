"""Resultado de um mês: recebimentos menos todas as despesas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FechamentoMensal:
    mes: str
    receitas_centavos: int
    despesas_centavos: int
    saldo_centavos: int

    @classmethod
    def calcular(cls, mes: str, receitas_centavos: int, despesas_centavos: int) -> "FechamentoMensal":
        return cls(
            mes=mes,
            receitas_centavos=receitas_centavos,
            despesas_centavos=despesas_centavos,
            saldo_centavos=receitas_centavos - despesas_centavos,
        )

    @classmethod
    def da_linha(cls, linha) -> "FechamentoMensal":
        return cls(
            mes=linha["closing_month"],
            receitas_centavos=linha["income_cents"],
            despesas_centavos=linha["expense_cents"],
            saldo_centavos=linha["balance_cents"],
        )
