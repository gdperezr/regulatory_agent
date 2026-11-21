"""Monta as abas do Streamlit e liga cada uma ao serviço."""

import streamlit as st

from meu_financeiro.banco.conexao_postgres import ConexaoPostgres
from meu_financeiro.excecoes_financeiras import ConfiguracaoAusente, ErroFinanceiro
from meu_financeiro.interface.pagina_cartoes import PaginaCartoes
from meu_financeiro.interface.pagina_compras import PaginaCompras
from meu_financeiro.interface.pagina_conta import PaginaConta
from meu_financeiro.interface.pagina_dashboard import PaginaDashboard
from meu_financeiro.interface.estilo_aplicativo import EstiloAplicativo
from meu_financeiro.interface.pagina_fechamento import PaginaFechamento
from meu_financeiro.interface.cookies_navegador import CookiesNavegador
from meu_financeiro.interface.pagina_login import PaginaLogin
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_autenticacao import COOKIE_LEMBRETE, ServicoAutenticacao
from meu_financeiro.servicos.servico_fechamento import ServicoFechamento
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class AplicativoFinanceiro:
    def __init__(
        self,
        servico: ServicoFinanceiro | None = None,
        autenticacao: ServicoAutenticacao | None = None,
    ):
        conexao = ConexaoPostgres()
        self._servico = servico or ServicoFinanceiro(conexao)
        self._autenticacao = autenticacao or ServicoAutenticacao(conexao)
        self._fechamento = ServicoFechamento(conexao)
        self._moeda = FormatadorMoeda()

    def executar(self) -> None:
        st.set_page_config(page_title="Meu Financeiro", page_icon="💳", layout="wide")
        EstiloAplicativo().aplicar()
        try:
            self._servico.inicializar()
            self._autenticacao.preparar()
        except ConfiguracaoAusente as erro:
            st.error(str(erro))
            return
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        cookies = CookiesNavegador()
        if not cookies.pronto():
            st.stop()
        self._restaurar_lembrete(cookies)
        if not PaginaLogin(self._autenticacao, cookies).exigir():
            return
        usuario_id = st.session_state["usuario_id"]
        eu = next((pessoa for pessoa in self._autenticacao.listar() if pessoa.id == usuario_id), None)
        nome = eu.nome if eu else st.session_state.get("usuario_nome", "")
        st.session_state["usuario_nome"] = nome
        EstiloAplicativo().topo(nome)
        aba_dashboard, aba_cartoes, aba_compras, aba_fechamento, aba_conta = st.tabs(
            ["Dashboard", "Cartões", "Compras", "Fechamento", "Conta"]
        )
        with aba_cartoes:
            PaginaCartoes(self._servico, self._moeda).exibir(usuario_id)
        with aba_compras:
            PaginaCompras(self._servico).exibir(usuario_id)
        with aba_dashboard:
            PaginaDashboard(self._servico, self._moeda).exibir(usuario_id)
        with aba_fechamento:
            PaginaFechamento(self._fechamento, self._moeda, self._servico).exibir(usuario_id)
        with aba_conta:
            PaginaConta(self._autenticacao, cookies).exibir()

    def _restaurar_lembrete(self, cookies: CookiesNavegador) -> None:
        if st.session_state.get("usuario_id"):
            return
        token = cookies.obter(COOKIE_LEMBRETE)
        if not token or st.session_state.get("lembrete_apagado"):
            return
        usuario = self._autenticacao.restaurar(token)
        if usuario is None:
            cookies.apagar(COOKIE_LEMBRETE)
            st.session_state["lembrete_apagado"] = True
            return
        st.session_state["usuario_id"] = usuario.id
        st.session_state["usuario_nome"] = usuario.nome
