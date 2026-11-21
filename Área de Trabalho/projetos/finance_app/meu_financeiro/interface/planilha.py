"""Lista lançamentos em colunas, com um traço sob cada linha."""

from contextlib import contextmanager
from html import escape

import streamlit as st


class Planilha:
    def __init__(self, chave: str):
        self._chave = chave
        self._bloco = None

    def __enter__(self):
        self._bloco = st.container(key=f"mf_lista_{self._chave}")
        self._bloco.__enter__()
        return self

    def __exit__(self, tipo, erro, rastreio):
        return self._bloco.__exit__(tipo, erro, rastreio)

    def cabecalho(self, titulos: list[str], pesos: list[float]) -> None:
        with st.container(key=f"mf_cabeca_{self._chave}"):
            colunas = st.columns(pesos, vertical_alignment="center")
            for coluna, titulo in zip(colunas, titulos):
                if titulo:
                    coluna.markdown(
                        f'<p class="mf-rotulo">{escape(titulo)}</p>',
                        unsafe_allow_html=True,
                    )

    @contextmanager
    def linha(self, textos: list[str], pesos: list[float], sufixo: str):
        with st.container(key=f"mf_linha_{self._chave}_{sufixo}"):
            colunas = st.columns(pesos, vertical_alignment="center")
            for coluna, texto in zip(colunas, textos):
                coluna.markdown(
                    f'<p class="mf-celula">{escape(texto)}</p>',
                    unsafe_allow_html=True,
                )
            yield tuple(colunas[len(textos) :])

    @contextmanager
    def resumo(self, nome: str, valor: str, meta: str, sufixo: str, com_acoes: bool = True):
        with st.container(key=f"mf_item_{self._chave}_{sufixo}"):
            coluna_nome, coluna_valor = st.columns([2.2, 1.2])
            coluna_nome.markdown(f'<p class="mf-item-nome">{escape(nome)}</p>', unsafe_allow_html=True)
            coluna_valor.markdown(f'<p class="mf-item-valor">{escape(valor)}</p>', unsafe_allow_html=True)
            if meta:
                st.markdown(f'<p class="mf-item-meta">{escape(meta)}</p>', unsafe_allow_html=True)
            if com_acoes:
                _, editar, apagar = st.columns([1.7, 1.15, 1.15])
                yield editar, apagar
            else:
                yield ()
