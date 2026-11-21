"""Sobe o PDF da fatura, mostra as despesas e grava as que você confirmar."""

from datetime import date

import pandas as pd
import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.leitor_fatura import LeitorFatura
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class PaginaImportacaoFatura:
    def __init__(self, servico: ServicoFinanceiro, formatador: FormatadorMoeda, leitor: LeitorFatura | None = None):
        self._servico = servico
        self._moeda = formatador
        self._leitor = leitor or LeitorFatura()

    def exibir(self, usuario_id: int) -> None:
        st.divider()
        st.subheader("Importar fatura do cartão")
        st.caption(
            "Envie o PDF baixado no Banco do Brasil, Itaú, Inter ou Santander. "
            "O programa lê as despesas e você confirma antes de gravar. "
            "Cada linha entra só no mês desta fatura. A parcela seguinte vem quando você subir a próxima, "
            "para não contar duas vezes."
        )
        cartoes = self._servico.listar_cartoes(usuario_id)
        if not cartoes:
            st.info("Cadastre primeiro um cartão na aba Cartões.")
            return
        opcoes = {cartao.nome: cartao.id for cartao in cartoes}
        nome_cartao = st.selectbox("Cartão da fatura", list(opcoes), key="cartao_fatura")
        mes = st.selectbox("Mês da fatura", self._meses(), index=0, key="mes_fatura_pdf")
        arquivo = st.file_uploader("PDF da fatura", type=["pdf"], key="pdf_fatura")
        if arquivo is None:
            st.session_state.pop("fatura_chave", None)
            return
        chave = f"{arquivo.name}:{arquivo.size}:{mes}"
        if st.session_state.get("fatura_chave") != chave:
            self._ler(arquivo.getvalue(), mes, chave)
        leitura = st.session_state.get("fatura_leitura")
        if leitura is None:
            return
        self._revisar(usuario_id, opcoes[nome_cartao], mes, leitura, chave)

    def _ler(self, conteudo: bytes, mes: str, chave: str) -> None:
        try:
            leitura = self._leitor.ler(conteudo, mes)
        except ErroFinanceiro as erro:
            st.session_state.pop("fatura_chave", None)
            st.session_state.pop("fatura_leitura", None)
            st.error(str(erro))
            return
        st.session_state["fatura_chave"] = chave
        st.session_state["fatura_leitura"] = leitura

    def _revisar(self, usuario_id: int, cartao_id: int, mes: str, leitura, chave: str) -> None:
        st.write(f"Banco reconhecido: **{leitura.banco}**. {len(leitura.lancamentos)} despesa(s) encontrada(s).")
        for aviso in leitura.avisos:
            st.warning(aviso)
        if leitura.ignorados:
            with st.expander(f"{len(leitura.ignorados)} linha(s) deixadas de fora"):
                for item in leitura.ignorados[:30]:
                    st.text(item)
        if not leitura.lancamentos:
            st.info("Nenhuma despesa para lançar. Os pagamentos e totais foram deixados de fora.")
            return
        tabela = pd.DataFrame(
            [
                {
                    "Importar": True,
                    "Data": item.data.strftime("%d/%m/%Y"),
                    "Descrição": item.descricao,
                    "Parcela": f"{item.numero_parcela}/{item.total_parcelas}",
                    "Valor": self._moeda.formatar(item.valor_centavos),
                }
                for item in leitura.lancamentos
            ]
        )
        editada = st.data_editor(
            tabela,
            hide_index=True,
            width="stretch",
            num_rows="fixed",
            disabled=["Data", "Descrição", "Parcela", "Valor"],
            key=f"editor_{chave}",
        )
        marcadas = editada["Importar"].tolist()
        selecionados = [item for item, marcado in zip(leitura.lancamentos, marcadas) if marcado]
        total = sum(item.valor_centavos for item in selecionados)
        st.caption(f"{len(selecionados)} selecionada(s), somando {self._moeda.formatar(total)}.")
        if st.button("Lançar na fatura", type="primary"):
            self._gravar(usuario_id, cartao_id, mes, selecionados)

    def _gravar(self, usuario_id: int, cartao_id: int, mes: str, selecionados) -> None:
        try:
            inseridos, repetidos = self._servico.importar_lancamentos_fatura(
                usuario_id, cartao_id, mes, selecionados
            )
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success(f"Lancei {inseridos} despesa(s) na fatura de {mes}.")
        if repetidos:
            st.info(f"{repetidos} já estavam lançadas e não foram repetidas.")

    def _meses(self) -> list[str]:
        ano = date.today().year
        mes = date.today().month
        meses = []
        for _ in range(13):
            meses.append(f"{ano:04d}-{mes:02d}")
            mes -= 1
            if mes == 0:
                ano -= 1
                mes = 12
        return meses
