"""Tela de entrada. Sem sessão válida, o restante do aplicativo não abre."""

import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.cookies_navegador import CookiesNavegador
from meu_financeiro.servicos.servico_autenticacao import (
    COOKIE_LEMBRETE,
    DURACAO_LEMBRETE,
    ServicoAutenticacao,
)


class PaginaLogin:
    def __init__(self, autenticacao: ServicoAutenticacao, cookies: CookiesNavegador):
        self._autenticacao = autenticacao
        self._cookies = cookies

    def exigir(self) -> bool:
        if st.session_state.get("usuario_id"):
            return True
        with st.container(key="cartao_login"):
            st.markdown('<p class="mf-kicker">Conta da casa</p>', unsafe_allow_html=True)
            st.markdown("<h1>Meu Financeiro</h1>", unsafe_allow_html=True)
            st.caption("Entre com o seu usuário e a sua senha.")
            with st.form("login_form"):
                login = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                lembrar = st.checkbox("Lembrar senha", value=True)
                entrar = st.form_submit_button("Entrar", type="primary", width="stretch")
        if entrar:
            self._entrar(login, senha, lembrar)
        if not self._autenticacao.listar():
            st.info("Ainda não há pessoas cadastradas.")
        return False

    def _entrar(self, login: str, senha: str, lembrar: bool) -> None:
        try:
            usuario = self._autenticacao.entrar(login, senha)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        self._guardar_lembrete(usuario.id, lembrar)
        st.session_state["usuario_id"] = usuario.id
        st.session_state["usuario_nome"] = usuario.nome
        st.rerun()

    def _guardar_lembrete(self, usuario_id: int, lembrar: bool) -> None:
        token_antigo = self._cookies.obter(COOKIE_LEMBRETE)
        if token_antigo:
            self._autenticacao.esquecer(token_antigo)
        if not lembrar:
            self._cookies.apagar(COOKIE_LEMBRETE)
            st.session_state["lembrete_apagado"] = True
            return
        token = self._autenticacao.lembrar(usuario_id)
        self._cookies.gravar(COOKIE_LEMBRETE, token, int(DURACAO_LEMBRETE.total_seconds()))
        st.session_state.pop("lembrete_apagado", None)
