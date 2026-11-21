"""Mostra a conta de quem entrou e cadastra outra pessoa, com finanças separadas."""

import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.cookies_navegador import CookiesNavegador
from meu_financeiro.servicos.servico_autenticacao import COOKIE_LEMBRETE, ServicoAutenticacao


class PaginaConta:
    def __init__(self, autenticacao: ServicoAutenticacao, cookies: CookiesNavegador):
        self._autenticacao = autenticacao
        self._cookies = cookies

    def exibir(self) -> None:
        usuario_id = st.session_state.get("usuario_id")
        eu = next((pessoa for pessoa in self._autenticacao.listar() if pessoa.id == usuario_id), None)
        nome = eu.nome if eu else st.session_state.get("usuario_nome", "")
        login = eu.login if eu else ""
        st.subheader(f"Olá, {nome}")
        if login:
            st.caption(f"Usuário: {login}")
        st.write("Seus cartões e suas compras ficam só nesta conta.")
        if st.button("Sair"):
            token = self._cookies.obter(COOKIE_LEMBRETE)
            if token:
                self._autenticacao.esquecer(token)
            self._cookies.apagar(COOKIE_LEMBRETE)
            st.session_state["lembrete_apagado"] = True
            st.session_state.pop("usuario_id", None)
            st.session_state.pop("usuario_nome", None)
            st.rerun()

        st.subheader("Cadastrar outra pessoa")
        st.caption("A conta nova começa vazia e não vê os lançamentos desta.")
        with st.form("nova_pessoa", clear_on_submit=True):
            nome_novo = st.text_input("Nome")
            login_novo = st.text_input("Usuário", placeholder="letras, números e _")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Salvar pessoa", type="primary"):
                self._salvar(nome_novo, login_novo, senha)

    def _salvar(self, nome: str, login: str, senha: str) -> None:
        try:
            self._autenticacao.cadastrar(nome, login, senha)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success("Pessoa cadastrada. Ela entra com o usuário e a senha dela, e vê só o que lançar.")
