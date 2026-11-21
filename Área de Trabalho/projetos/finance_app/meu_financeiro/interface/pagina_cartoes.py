"""Aba de cadastro e listagem de cartões."""

import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.planilha import Planilha
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class PaginaCartoes:
    def __init__(self, servico: ServicoFinanceiro, formatador: FormatadorMoeda):
        self._servico = servico
        self._moeda = formatador

    def exibir(self, usuario_id: int) -> None:
        st.subheader("Cadastrar cartão")
        with st.form("card_form", clear_on_submit=True):
            nome = st.text_input("Nome do cartão", placeholder="Ex.: Banco do Brasil Visa")
            limite = st.number_input("Limite (R$)", min_value=0.0, step=100.0, format="%.2f")
            coluna_fechamento, coluna_vencimento = st.columns(2)
            with coluna_fechamento:
                fechamento = st.number_input("Dia de fechamento", min_value=1, max_value=31, value=10)
            with coluna_vencimento:
                vencimento = st.number_input("Dia de vencimento", min_value=1, max_value=31, value=17)
            if st.form_submit_button("Salvar cartão", type="primary"):
                self._salvar(usuario_id, nome, limite, int(fechamento), int(vencimento))
        self._listar(usuario_id)

    def _salvar(self, usuario_id: int, nome: str, limite: float, fechamento: int, vencimento: int) -> None:
        try:
            self._servico.cadastrar_cartao(usuario_id, nome, limite, fechamento, vencimento)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success("Cartão cadastrado!")

    def _listar(self, usuario_id: int) -> None:
        self._descartar_campos()
        cartoes = self._servico.listar_cartoes(usuario_id)
        st.subheader("Meus cartões")
        if not cartoes:
            st.caption("Nenhum cartão cadastrado.")
            return
        with Planilha("cartoes") as tabela:
            for cartao in cartoes:
                with tabela.resumo(
                    cartao.nome,
                    self._moeda.formatar(cartao.limite_centavos),
                    f"Fecha dia {cartao.dia_fechamento} · Vence dia {cartao.dia_vencimento}",
                    str(cartao.id),
                ) as (editar, apagar):
                    if editar.button("Editar", key=f"editar-cartao-{cartao.id}", width="content"):
                        st.session_state["cartao_em_edicao"] = cartao.id
                    if apagar.button("Apagar", key=f"apagar-cartao-{cartao.id}", width="content"):
                        self._apagar(usuario_id, cartao.id)
                if st.session_state.get("cartao_em_edicao") == cartao.id:
                    self._editar(usuario_id, cartao)

    def _editar(self, usuario_id: int, cartao) -> None:
        st.caption("O novo dia de fechamento vale para as próximas compras.")
        with st.form(f"editar-cartao-{cartao.id}"):
            nome = st.text_input("Nome do cartão", value=cartao.nome, key=f"cartao-nome-{cartao.id}")
            limite = st.number_input(
                "Limite (R$)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=cartao.limite_centavos / 100,
                key=f"cartao-limite-{cartao.id}",
            )
            coluna_fechamento, coluna_vencimento = st.columns(2)
            with coluna_fechamento:
                fechamento = st.number_input(
                    "Dia de fechamento",
                    min_value=1,
                    max_value=31,
                    value=cartao.dia_fechamento,
                    key=f"cartao-fecha-{cartao.id}",
                )
            with coluna_vencimento:
                vencimento = st.number_input(
                    "Dia de vencimento",
                    min_value=1,
                    max_value=31,
                    value=cartao.dia_vencimento,
                    key=f"cartao-vence-{cartao.id}",
                )
            coluna_salvar, coluna_cancelar = st.columns(2)
            salvar = coluna_salvar.form_submit_button("Salvar", type="primary")
            cancelar = coluna_cancelar.form_submit_button("Cancelar")
        if cancelar:
            self._fechar_edicao(cartao.id)
        if salvar:
            self._atualizar(usuario_id, cartao.id, nome, limite, int(fechamento), int(vencimento))

    def _atualizar(
        self,
        usuario_id: int,
        cartao_id: int,
        nome: str,
        limite: float,
        fechamento: int,
        vencimento: int,
    ) -> None:
        try:
            self._servico.atualizar_cartao(usuario_id, cartao_id, nome, limite, fechamento, vencimento)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        self._fechar_edicao(cartao_id)

    def _apagar(self, usuario_id: int, cartao_id: int) -> None:
        try:
            self._servico.remover_cartao(usuario_id, cartao_id)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        if st.session_state.get("cartao_em_edicao") == cartao_id:
            self._fechar_edicao(cartao_id)
            return
        st.rerun()

    def _fechar_edicao(self, cartao_id: int) -> None:
        st.session_state.pop("cartao_em_edicao", None)
        st.session_state["limpar_cartao"] = cartao_id
        st.rerun()

    def _descartar_campos(self) -> None:
        cartao_id = st.session_state.pop("limpar_cartao", None)
        if cartao_id is None:
            return
        for chave in (
            f"cartao-nome-{cartao_id}",
            f"cartao-limite-{cartao_id}",
            f"cartao-fecha-{cartao_id}",
            f"cartao-vence-{cartao_id}",
        ):
            st.session_state.pop(chave, None)
