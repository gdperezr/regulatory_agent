"""Abre transações no PostgreSQL a partir de DATABASE_URL."""

import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from meu_financeiro.excecoes_financeiras import ConfiguracaoAusente


class ConexaoPostgres:
    """Cada uso de `transacao` confirma ou desfaz as alterações juntas."""

    def __init__(self, url: str | None = None):
        self.url = url if url is not None else os.environ.get("DATABASE_URL", "").strip()

    @contextmanager
    def transacao(self):
        if not self.url:
            raise ConfiguracaoAusente(
                "Defina DATABASE_URL com a conexão do PostgreSQL. "
                "No computador, use docker compose. Na Oracle Cloud, o mesmo arquivo sobe o banco."
            )
        conn = psycopg.connect(self.url, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
