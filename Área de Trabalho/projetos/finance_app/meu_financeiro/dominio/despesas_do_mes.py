"""Todas as despesas de um mês: faturas do cartão e custos fixos."""

from dataclasses import dataclass

from meu_financeiro.dominio.custo_fixo import CustoFixo
from meu_financeiro.dominio.detalhe_fatura import DetalheFatura


@dataclass(frozen=True)
class DespesasDoMes:
    mes: str
    faturas: list[DetalheFatura]
    custos_fixos: list[CustoFixo]

    @property
    def total_faturas_centavos(self) -> int:
        return sum(item.valor_centavos for item in self.faturas)

    @property
    def total_custos_fixos_centavos(self) -> int:
        return sum(custo.valor_centavos for custo in self.custos_fixos)

    @property
    def total_centavos(self) -> int:
        return self.total_faturas_centavos + self.total_custos_fixos_centavos
