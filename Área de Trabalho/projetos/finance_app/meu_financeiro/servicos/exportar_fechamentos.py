"""Monta a planilha XLSX com todos os fechamentos salvos."""

from io import BytesIO

import pandas as pd

from meu_financeiro.dominio.despesas_do_mes import DespesasDoMes
from meu_financeiro.dominio.fechamento_mensal import FechamentoMensal
from meu_financeiro.dominio.recebimento import Recebimento


def _reais(centavos: int) -> float:
    return round(centavos / 100, 2)


def gerar_xlsx(
    fechamentos: list[FechamentoMensal],
    detalhes: dict[str, tuple[list[Recebimento], DespesasDoMes]],
) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "Mês": item.mes,
                    "Recebimentos (R$)": _reais(item.receitas_centavos),
                    "Despesas (R$)": _reais(item.despesas_centavos),
                    "Saldo (R$)": _reais(item.saldo_centavos),
                }
                for item in fechamentos
            ]
        ).to_excel(writer, sheet_name="Resumo", index=False)

        for fechamento in fechamentos:
            recebimentos, despesas = detalhes[fechamento.mes]
            linhas: list[dict] = []
            for item in recebimentos:
                linhas.append(
                    {
                        "Tipo": "Recebimento",
                        "Cartão": "",
                        "Descrição": item.descricao,
                        "Data": "",
                        "Parcela": "",
                        "Valor (R$)": _reais(item.valor_centavos),
                    }
                )
            for item in despesas.faturas:
                linhas.append(
                    {
                        "Tipo": "Fatura",
                        "Cartão": item.cartao,
                        "Descrição": item.descricao,
                        "Data": item.data_compra,
                        "Parcela": f"{item.numero_parcela}/{item.total_parcelas}",
                        "Valor (R$)": _reais(item.valor_centavos),
                    }
                )
            for custo in despesas.custos_fixos:
                linhas.append(
                    {
                        "Tipo": "Custo fixo",
                        "Cartão": "",
                        "Descrição": custo.descricao,
                        "Data": "",
                        "Parcela": "",
                        "Valor (R$)": _reais(custo.valor_centavos),
                    }
                )
            linhas.append(
                {
                    "Tipo": "Total",
                    "Cartão": "",
                    "Descrição": "Recebimentos",
                    "Data": "",
                    "Parcela": "",
                    "Valor (R$)": _reais(fechamento.receitas_centavos),
                }
            )
            linhas.append(
                {
                    "Tipo": "Total",
                    "Cartão": "",
                    "Descrição": "Despesas",
                    "Data": "",
                    "Parcela": "",
                    "Valor (R$)": _reais(fechamento.despesas_centavos),
                }
            )
            linhas.append(
                {
                    "Tipo": "Total",
                    "Cartão": "",
                    "Descrição": "Saldo",
                    "Data": "",
                    "Parcela": "",
                    "Valor (R$)": _reais(fechamento.saldo_centavos),
                }
            )
            pd.DataFrame(linhas).to_excel(writer, sheet_name=fechamento.mes[:31], index=False)

    return buffer.getvalue()
