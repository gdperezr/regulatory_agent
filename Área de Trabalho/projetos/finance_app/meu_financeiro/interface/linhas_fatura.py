"""Edita ou apaga cada parcela visível numa fatura."""

from datetime import date
from html import escape

import streamlit as st

from meu_financeiro.dominio.detalhe_fatura import DetalheFatura
from meu_financeiro.excecoes_financeiras import ErroFinanceiro
from meu_financeiro.interface.planilha import Planilha
from meu_financeiro.servicos.formatador_moeda import FormatadorMoeda
from meu_financeiro.servicos.servico_financeiro import ServicoFinanceiro


class LinhasFatura:
    def __init__(self, servico: ServicoFinanceiro, formatador: FormatadorMoeda, prefixo: str):
        self._servico = servico
        self._moeda = formatador
        self._prefixo = prefixo

    def exibir(self, usuario_id: int, detalhes: list[DetalheFatura], resumido: bool = False) -> None:
        self._descartar_campos()
        if not detalhes:
            st.caption("Nenhuma parcela neste mês.")
            return
        if resumido:
            self._exibir_resumido(usuario_id, detalhes)
            return
        pesos = [2.1, 2.2, 1.3, 1, 1.4, 1.1, 1.1]
        with Planilha(f"fatura_{self._prefixo}") as tabela:
            tabela.cabecalho(["Cartão", "Descrição", "Data", "Parcela", "Valor", "", ""], pesos)
            for detalhe in detalhes:
                self._linha(usuario_id, detalhe, tabela, pesos)

    def _exibir_resumido(self, usuario_id: int, detalhes: list[DetalheFatura]) -> None:
        with st.container(key=f"mf_lista_{self._prefixo}"):
            for detalhe in detalhes:
                self._item_resumido(usuario_id, detalhe)

    def _item_resumido(self, usuario_id: int, detalhe: DetalheFatura) -> None:
        chave = f"{self._prefixo}-{detalhe.item_id}"
        data = date.fromisoformat(detalhe.data_compra[:10]).strftime("%d/%m/%Y")
        meta = f"{detalhe.cartao} · {data} · {detalhe.numero_parcela}/{detalhe.total_parcelas}"
        with st.container(key=f"mf_item_{chave}"):
            coluna_nome, coluna_valor = st.columns([2.2, 1.2])
            coluna_nome.markdown(
                f'<p class="mf-item-nome">{escape(detalhe.descricao)}</p>',
                unsafe_allow_html=True,
            )
            coluna_valor.markdown(
                f'<p class="mf-item-valor">{escape(self._moeda.formatar(detalhe.valor_centavos))}</p>',
                unsafe_allow_html=True,
            )
            st.markdown(f'<p class="mf-item-meta">{escape(meta)}</p>', unsafe_allow_html=True)
            _, coluna_editar, coluna_apagar = st.columns([1.7, 1.15, 1.15])
            if coluna_editar.button("Editar", key=f"editar-{chave}", width="content"):
                st.session_state[f"parcela_em_edicao_{self._prefixo}"] = detalhe.item_id
            if coluna_apagar.button("Apagar", key=f"apagar-{chave}", width="content"):
                self._apagar(usuario_id, detalhe.item_id)
        if st.session_state.get(f"parcela_em_edicao_{self._prefixo}") == detalhe.item_id:
            self._editar(usuario_id, detalhe, chave)

    def _linha(self, usuario_id: int, detalhe: DetalheFatura, tabela: Planilha, pesos: list[float]) -> None:
        chave = f"{self._prefixo}-{detalhe.item_id}"
        data = date.fromisoformat(detalhe.data_compra[:10]).strftime("%d/%m/%Y")
        with tabela.linha(
            [
                detalhe.cartao,
                detalhe.descricao,
                data,
                f"{detalhe.numero_parcela}/{detalhe.total_parcelas}",
                self._moeda.formatar(detalhe.valor_centavos),
            ],
            pesos,
            chave,
        ) as (editar, apagar):
            if editar.button("Editar", key=f"editar-{chave}", width="content"):
                st.session_state[f"parcela_em_edicao_{self._prefixo}"] = detalhe.item_id
            if apagar.button("Apagar", key=f"apagar-{chave}", width="content"):
                self._apagar(usuario_id, detalhe.item_id)
        if st.session_state.get(f"parcela_em_edicao_{self._prefixo}") == detalhe.item_id:
            self._editar(usuario_id, detalhe, chave)

    def _editar(self, usuario_id: int, detalhe: DetalheFatura, chave: str) -> None:
        st.caption("A descrição e a data valem para a compra inteira. O valor muda só esta parcela.")
        with st.form(f"form-{chave}"):
            descricao = st.text_input("Descrição", value=detalhe.descricao, key=f"desc-{chave}")
            data_compra = st.date_input(
                "Data da compra",
                value=date.fromisoformat(detalhe.data_compra[:10]),
                key=f"data-{chave}",
            )
            valor = st.number_input(
                "Valor desta parcela (R$)",
                min_value=0.01,
                step=10.0,
                format="%.2f",
                value=detalhe.valor_centavos / 100,
                key=f"valor-{chave}",
            )
            coluna_salvar, coluna_cancelar = st.columns(2)
            salvar = coluna_salvar.form_submit_button("Salvar", type="primary")
            cancelar = coluna_cancelar.form_submit_button("Cancelar")
        if cancelar:
            self._fechar(detalhe.item_id, chave)
        if salvar:
            self._atualizar(usuario_id, detalhe.item_id, chave, descricao, data_compra, valor)

    def _atualizar(
        self,
        usuario_id: int,
        parcela_id: int,
        chave: str,
        descricao: str,
        data_compra: date,
        valor: float,
    ) -> None:
        try:
            self._servico.atualizar_parcela(usuario_id, parcela_id, descricao, data_compra, valor)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        self._fechar(parcela_id, chave)

    def _apagar(self, usuario_id: int, parcela_id: int) -> None:
        try:
            self._servico.remover_parcela(usuario_id, parcela_id)
        except ErroFinanceiro as erro:
            st.error(str(erro))
            return
        if st.session_state.get(f"parcela_em_edicao_{self._prefixo}") == parcela_id:
            self._fechar(parcela_id, f"{self._prefixo}-{parcela_id}")
            return
        st.rerun()

    def _fechar(self, parcela_id: int, chave: str) -> None:
        st.session_state.pop(f"parcela_em_edicao_{self._prefixo}", None)
        st.session_state[f"limpar_parcela_{self._prefixo}"] = (parcela_id, chave)
        st.rerun()

    def _descartar_campos(self) -> None:
        pendente = st.session_state.pop(f"limpar_parcela_{self._prefixo}", None)
        if pendente is None:
            return
        _, chave = pendente
        for campo in (f"desc-{chave}", f"data-{chave}", f"valor-{chave}"):
            st.session_state.pop(campo, None)
