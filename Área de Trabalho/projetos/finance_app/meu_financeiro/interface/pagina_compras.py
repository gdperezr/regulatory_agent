"""Aba de cadastro de compras parceladas."""

from datetime import date

import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.pagina_importacao_fatura import PaginaImportacaoFatura
from meu_financeiro.interface.planilha import Planilha
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class PaginaCompras:
    def __init__(self, servico: ServicoFinanceiro):
        self._servico = servico

    def exibir(self, usuario_id: int) -> None:
        st.subheader("Cadastrar compra")
        cartoes = self._servico.listar_cartoes(usuario_id)
        if not cartoes:
            st.info("Cadastre primeiro um cartão na aba Cartões.")
            return
        opcoes = {cartao.nome: cartao.id for cartao in cartoes}
        with st.form("purchase_form", clear_on_submit=True):
            nome_cartao = st.selectbox("Cartão", list(opcoes))
            descricao = st.text_input("Descrição", placeholder="Ex.: Supermercado")
            data_compra = st.date_input("Data da compra", value=date.today())
            total = st.number_input("Valor total (R$)", min_value=0.01, step=10.0, format="%.2f")
            parcelas = st.number_input("Número de parcelas", min_value=1, max_value=120, value=1)
            st.caption("Compra no dia do fechamento ou depois entra na fatura do mês seguinte.")
            if st.form_submit_button("Salvar compra", type="primary"):
                self._salvar(usuario_id, opcoes[nome_cartao], descricao, data_compra, total, int(parcelas))
        self._listar(usuario_id, opcoes)
        PaginaImportacaoFatura(self._servico, FormatadorMoeda()).exibir(usuario_id)

    def _salvar(
        self,
        usuario_id: int,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total: float,
        parcelas: int,
    ) -> None:
        try:
            self._servico.cadastrar_compra(usuario_id, cartao_id, descricao, data_compra, total, parcelas)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success("Compra cadastrada e parcelas distribuídas nas faturas!")

    def _listar(self, usuario_id: int, opcoes: dict[str, int]) -> None:
        self._descartar_campos()
        compras = self._servico.listar_compras(usuario_id)
        st.subheader("Compras lançadas")
        st.caption(
            "Editar uma compra feita aqui redistribui o valor nas parcelas. "
            "Uma linha vinda da fatura muda só naquele mês."
        )
        if not compras:
            st.caption("Nenhuma compra lançada.")
            return
        moeda = FormatadorMoeda()
        with Planilha("compras") as tabela:
            for compra in compras:
                parcelas = "À vista" if compra.parcelas == 1 else f"{compra.parcelas}x"
                with tabela.resumo(
                    compra.descricao,
                    moeda.formatar(compra.total_centavos),
                    f"{compra.cartao} · {compra.data_compra.strftime('%d/%m/%Y')} · {parcelas}",
                    str(compra.id),
                ) as (editar, apagar):
                    if editar.button("Editar", key=f"editar-compra-{compra.id}", width="content"):
                        st.session_state["compra_em_edicao"] = compra.id
                    if apagar.button("Apagar", key=f"apagar-compra-{compra.id}", width="content"):
                        self._apagar(usuario_id, compra.id)
                if st.session_state.get("compra_em_edicao") == compra.id:
                    self._editar(usuario_id, compra, opcoes)

    def _editar(self, usuario_id: int, compra, opcoes: dict[str, int]) -> None:
        nomes = list(opcoes)
        indice = nomes.index(compra.cartao) if compra.cartao in nomes else 0
        with st.form(f"editar-compra-{compra.id}"):
            nome_cartao = st.selectbox("Cartão", nomes, index=indice, key=f"compra-cartao-{compra.id}")
            descricao = st.text_input("Descrição", value=compra.descricao, key=f"compra-desc-{compra.id}")
            data_compra = st.date_input("Data da compra", value=compra.data_compra, key=f"compra-data-{compra.id}")
            total = st.number_input(
                "Valor total (R$)",
                min_value=0.01,
                step=10.0,
                format="%.2f",
                value=compra.total_centavos / 100,
                key=f"compra-total-{compra.id}",
            )
            parcelas = st.number_input(
                "Número de parcelas",
                min_value=1,
                max_value=120,
                value=compra.parcelas,
                key=f"compra-parcelas-{compra.id}",
            )
            coluna_salvar, coluna_cancelar = st.columns(2)
            salvar = coluna_salvar.form_submit_button("Salvar", type="primary")
            cancelar = coluna_cancelar.form_submit_button("Cancelar")
        if cancelar:
            self._fechar_edicao(compra.id)
        if salvar:
            self._atualizar(
                usuario_id,
                compra.id,
                opcoes[nome_cartao],
                descricao,
                data_compra,
                total,
                int(parcelas),
            )

    def _atualizar(
        self,
        usuario_id: int,
        compra_id: int,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total: float,
        parcelas: int,
    ) -> None:
        try:
            self._servico.atualizar_compra(
                usuario_id, compra_id, cartao_id, descricao, data_compra, total, parcelas
            )
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        self._fechar_edicao(compra_id)

    def _apagar(self, usuario_id: int, compra_id: int) -> None:
        try:
            self._servico.remover_compra(usuario_id, compra_id)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        if st.session_state.get("compra_em_edicao") == compra_id:
            self._fechar_edicao(compra_id)
            return
        st.rerun()

    def _fechar_edicao(self, compra_id: int) -> None:
        st.session_state.pop("compra_em_edicao", None)
        st.session_state["limpar_compra"] = compra_id
        st.rerun()

    def _descartar_campos(self) -> None:
        compra_id = st.session_state.pop("limpar_compra", None)
        if compra_id is None:
            return
        for chave in (
            f"compra-cartao-{compra_id}",
            f"compra-desc-{compra_id}",
            f"compra-data-{compra_id}",
            f"compra-total-{compra_id}",
            f"compra-parcelas-{compra_id}",
        ):
            st.session_state.pop(chave, None)
