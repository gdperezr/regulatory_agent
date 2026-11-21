"""Aba com totais do mês, próximos meses e detalhe da fatura."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from meu_financeiro.interface.linhas_fatura import LinhasFatura
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class PaginaDashboard:
    def __init__(self, servico: ServicoFinanceiro, formatador: FormatadorMoeda):
        self._servico = servico
        self._moeda = formatador

    def exibir(self, usuario_id: int) -> None:
        resumos = self._servico.resumir_faturas(usuario_id)
        if not resumos:
            st.info("Cadastre um cartão e uma compra para visualizar suas faturas.")
            return

        tabela = pd.DataFrame(
            [
                {
                    "invoice_month": resumo.mes_fatura,
                    "card": resumo.cartao,
                    "amount_cents": resumo.valor_centavos,
                    "Valor": resumo.valor_centavos / 100,
                }
                for resumo in resumos
            ]
        )
        mes_atual = date.today().strftime("%Y-%m")
        atual = int(tabela.loc[tabela.invoice_month == mes_atual, "amount_cents"].sum())
        futuro = int(tabela.loc[tabela.invoice_month > mes_atual, "amount_cents"].sum())

        with st.container(key="mf_dash"):
            coluna_mes, coluna_futuro, coluna_total = st.columns(3)
            coluna_mes.metric("Faturas do mês", self._moeda.formatar(atual))
            coluna_futuro.metric("Próximos meses", self._moeda.formatar(futuro))
            coluna_total.metric("Total cadastrado", self._moeda.formatar(int(tabela.amount_cents.sum())))

            por_mes = tabela.groupby("invoice_month", as_index=False)["Valor"].sum()
            por_mes = por_mes.rename(columns={"invoice_month": "Mês"})
            por_mes["Rotulo"] = por_mes["Mês"].map(self._rotulo_mes)
            st.subheader("Faturas por mês")
            st.altair_chart(self._grafico(por_mes), width="stretch")
            st.subheader("Lançamentos")
            meses = sorted(tabela.invoice_month.unique().tolist())
            indice = meses.index(mes_atual) if mes_atual in meses else 0
            selecionado = st.selectbox("Mês da fatura", meses, index=indice)
            self._detalhar(usuario_id, selecionado)
            st.caption("Apagar tira só aquela linha. Para mudar o total e redistribuir, use a aba Compras.")

    def _detalhar(self, usuario_id: int, mes_fatura: str) -> None:
        detalhes = self._servico.detalhar_fatura(usuario_id, mes_fatura)
        LinhasFatura(self._servico, self._moeda, "dash").exibir(usuario_id, detalhes, resumido=True)

    def _rotulo_mes(self, valor: str) -> str:
        nomes = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
        ano, mes = valor.split("-")
        return f"{nomes[int(mes) - 1]}/{ano[2:]}"

    def _grafico(self, por_mes: pd.DataFrame) -> alt.Chart:
        return (
            alt.Chart(por_mes)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#1f6b4a")
            .encode(
                x=alt.X("Rotulo:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelPadding=4)),
                y=alt.Y("Valor:Q", title=None),
                tooltip=[alt.Tooltip("Mês:N", title="Mês"), alt.Tooltip("Valor:Q", format=",.2f")],
            )
            .properties(height=180)
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor="#5e675f", labelFontSize=11, gridColor="#efe8dc", domain=False)
        )
