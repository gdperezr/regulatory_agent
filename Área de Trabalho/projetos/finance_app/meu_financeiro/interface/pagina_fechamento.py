"""Cadastro de custos fixos e recebimentos, e o fechamento do mês."""

from datetime import date

import streamlit as st

from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.linhas_fatura import LinhasFatura
from meu_financeiro.interface.planilha import Planilha
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_fechamento import ServicoFechamento
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class PaginaFechamento:
    def __init__(
        self,
        servico: ServicoFechamento,
        formatador: FormatadorMoeda,
        financeiro: ServicoFinanceiro,
    ):
        self._servico = servico
        self._moeda = formatador
        self._financeiro = financeiro

    def exibir(self, usuario_id: int) -> None:
        mes = st.selectbox("Mês", self._meses(), index=0)
        self._custos(usuario_id)
        self._recebimentos(usuario_id, mes)
        coluna_despesas, coluna_fechar = st.columns(2)
        with coluna_despesas:
            ver_despesas = st.button("Realizar fechamento", width="stretch")
        with coluna_fechar:
            fechar = st.button("Fechar mês", type="primary", width="stretch")
        if ver_despesas:
            st.session_state["fechamento_despesas"] = mes
        if fechar:
            st.session_state["fechamento_resultado"] = mes
        if st.session_state.get("fechamento_despesas") == mes:
            self._mostrar_despesas(usuario_id, mes)
        if st.session_state.get("fechamento_resultado") == mes:
            self._fechar(usuario_id, mes)
        self._baixados(usuario_id)

    def _custos(self, usuario_id: int) -> None:
        self._descartar_custo()
        st.subheader("Custos fixos")
        st.caption("Entram em todo mês até você remover.")
        with st.form("custo_fixo", clear_on_submit=True):
            descricao = st.text_input("Descrição", placeholder="Ex.: Aluguel", key="descricao_custo")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f", key="valor_custo")
            if st.form_submit_button("Salvar custo fixo", type="primary"):
                self._salvar_custo(usuario_id, descricao, valor)
        custos = self._servico.listar_custos_fixos(usuario_id)
        if not custos:
            st.info("Nenhum custo fixo cadastrado.")
            return
        with Planilha("custos") as tabela:
            for custo in custos:
                with tabela.resumo(
                    custo.descricao,
                    self._moeda.formatar(custo.valor_centavos),
                    "",
                    str(custo.id),
                ) as (editar, apagar):
                    if editar.button("Editar", key=f"editar-custo-{custo.id}", width="content"):
                        st.session_state["custo_em_edicao"] = custo.id
                    if apagar.button("Apagar", key=f"custo-{custo.id}", width="content"):
                        self._servico.remover_custo_fixo(usuario_id, custo.id)
                        if st.session_state.get("custo_em_edicao") == custo.id:
                            self._fechar_custo(custo.id)
                        st.rerun()
                if st.session_state.get("custo_em_edicao") == custo.id:
                    self._editar_custo(usuario_id, custo)

    def _recebimentos(self, usuario_id: int, mes: str) -> None:
        self._descartar_recebimento()
        st.subheader(f"Recebimentos de {mes}")
        with st.form("recebimento", clear_on_submit=True):
            descricao = st.text_input("Descrição", placeholder="Ex.: Salário", key="descricao_recebimento")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=100.0, format="%.2f", key="valor_recebimento")
            if st.form_submit_button("Salvar recebimento", type="primary"):
                self._salvar_recebimento(usuario_id, descricao, valor, mes)
        recebimentos = self._servico.listar_recebimentos(usuario_id, mes)
        if not recebimentos:
            st.info("Nenhum recebimento neste mês.")
            return
        with Planilha("recebimentos") as tabela:
            for item in recebimentos:
                with tabela.resumo(
                    item.descricao,
                    self._moeda.formatar(item.valor_centavos),
                    "",
                    str(item.id),
                ) as (editar, apagar):
                    if editar.button("Editar", key=f"editar-recebimento-{item.id}", width="content"):
                        st.session_state["recebimento_em_edicao"] = item.id
                    if apagar.button("Apagar", key=f"recebimento-{item.id}", width="content"):
                        self._servico.remover_recebimento(usuario_id, item.id)
                        if st.session_state.get("recebimento_em_edicao") == item.id:
                            self._fechar_recebimento(item.id)
                        st.rerun()
                if st.session_state.get("recebimento_em_edicao") == item.id:
                    self._editar_recebimento(usuario_id, item)

    def _mostrar_despesas(self, usuario_id: int, mes: str) -> None:
        despesas = self._servico.despesas_do_mes(usuario_id, mes)
        st.subheader(f"Despesas de {mes}")
        st.markdown("**Faturas do cartão**")
        LinhasFatura(self._financeiro, self._moeda, "fecha").exibir(usuario_id, despesas.faturas, resumido=True)
        st.markdown("**Custos fixos**")
        if despesas.custos_fixos:
            with Planilha("custos_resumo") as tabela:
                for custo in despesas.custos_fixos:
                    with tabela.resumo(
                        custo.descricao,
                        self._moeda.formatar(custo.valor_centavos),
                        "",
                        str(custo.id),
                        com_acoes=False,
                    ):
                        pass
        else:
            st.caption("Nenhum custo fixo.")
        st.metric("Total de despesas", self._moeda.formatar(despesas.total_centavos))

    def _fechar(self, usuario_id: int, mes: str) -> None:
        fechamento = self._servico.fechar_mes(usuario_id, mes)
        st.subheader(f"Resultado de {mes}")
        coluna_receita, coluna_despesa, coluna_saldo = st.columns(3)
        coluna_receita.metric("Recebimentos", self._moeda.formatar(fechamento.receitas_centavos))
        coluna_despesa.metric("Despesas", self._moeda.formatar(fechamento.despesas_centavos))
        titulo = "Sobra" if fechamento.saldo_centavos >= 0 else "Falta"
        coluna_saldo.metric(titulo, self._moeda.formatar(abs(fechamento.saldo_centavos)))
        st.caption("Despesas = faturas do cartão neste mês + custos fixos. Recebimentos são só os deste mês.")

    def _baixados(self, usuario_id: int) -> None:
        st.subheader("Fechamentos salvos")
        fechamentos = self._servico.listar_fechamentos(usuario_id)
        if not fechamentos:
            st.caption("Nenhum mês fechado ainda. Use Fechar mês para gravar.")
            return
        with Planilha("fechamentos_salvos") as tabela:
            for item in fechamentos:
                with tabela.resumo(
                    item.mes,
                    self._moeda.formatar(item.saldo_centavos),
                    (
                        f"Receb. {self._moeda.formatar(item.receitas_centavos)}"
                        f" · Desp. {self._moeda.formatar(item.despesas_centavos)}"
                    ),
                    item.mes,
                    com_acoes=False,
                ):
                    pass
        arquivo = self._servico.exportar_fechamentos_xlsx(usuario_id)
        st.download_button(
            "Baixar todos em XLSX",
            data=arquivo,
            file_name="fechamentos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

    def _editar_custo(self, usuario_id: int, custo) -> None:
        with st.form(f"editar-custo-{custo.id}"):
            descricao = st.text_input("Descrição", value=custo.descricao, key=f"custo-desc-{custo.id}")
            valor = st.number_input(
                "Valor (R$)",
                min_value=0.01,
                step=10.0,
                format="%.2f",
                value=custo.valor_centavos / 100,
                key=f"custo-valor-{custo.id}",
            )
            coluna_salvar, coluna_cancelar = st.columns(2)
            salvar = coluna_salvar.form_submit_button("Salvar", type="primary")
            cancelar = coluna_cancelar.form_submit_button("Cancelar")
        if cancelar:
            self._fechar_custo(custo.id)
        if salvar:
            try:
                self._servico.atualizar_custo_fixo(usuario_id, custo.id, descricao, valor)
            except ErroFinanceiro as erro:
                st.error(str(erro))
                return
            self._fechar_custo(custo.id)

    def _fechar_custo(self, custo_id: int) -> None:
        st.session_state.pop("custo_em_edicao", None)
        st.session_state["limpar_custo"] = custo_id
        st.rerun()

    def _descartar_custo(self) -> None:
        custo_id = st.session_state.pop("limpar_custo", None)
        if custo_id is None:
            return
        st.session_state.pop(f"custo-desc-{custo_id}", None)
        st.session_state.pop(f"custo-valor-{custo_id}", None)

    def _editar_recebimento(self, usuario_id: int, item) -> None:
        meses = self._meses()
        indice = meses.index(item.mes) if item.mes in meses else 0
        with st.form(f"editar-recebimento-{item.id}"):
            descricao = st.text_input("Descrição", value=item.descricao, key=f"receb-desc-{item.id}")
            valor = st.number_input(
                "Valor (R$)",
                min_value=0.01,
                step=100.0,
                format="%.2f",
                value=item.valor_centavos / 100,
                key=f"receb-valor-{item.id}",
            )
            mes = st.selectbox("Mês", meses, index=indice, key=f"receb-mes-{item.id}")
            coluna_salvar, coluna_cancelar = st.columns(2)
            salvar = coluna_salvar.form_submit_button("Salvar", type="primary")
            cancelar = coluna_cancelar.form_submit_button("Cancelar")
        if cancelar:
            self._fechar_recebimento(item.id)
        if salvar:
            try:
                self._servico.atualizar_recebimento(usuario_id, item.id, descricao, valor, mes)
            except ErroFinanceiro as erro:
                st.error(str(erro))
                return
            self._fechar_recebimento(item.id)

    def _fechar_recebimento(self, recebimento_id: int) -> None:
        st.session_state.pop("recebimento_em_edicao", None)
        st.session_state["limpar_recebimento"] = recebimento_id
        st.rerun()

    def _descartar_recebimento(self) -> None:
        recebimento_id = st.session_state.pop("limpar_recebimento", None)
        if recebimento_id is None:
            return
        st.session_state.pop(f"receb-desc-{recebimento_id}", None)
        st.session_state.pop(f"receb-valor-{recebimento_id}", None)
        st.session_state.pop(f"receb-mes-{recebimento_id}", None)

    def _salvar_custo(self, usuario_id: int, descricao: str, valor: float) -> None:
        try:
            self._servico.cadastrar_custo_fixo(usuario_id, descricao, valor)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success("Custo fixo cadastrado.")

    def _salvar_recebimento(self, usuario_id: int, descricao: str, valor: float, mes: str) -> None:
        try:
            self._servico.cadastrar_recebimento(usuario_id, descricao, valor, mes)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        st.success("Recebimento cadastrado.")

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
