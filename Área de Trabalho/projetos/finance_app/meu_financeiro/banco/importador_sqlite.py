"""Copia o financeiro.db local para o PostgreSQL, uma vez, se o banco novo estiver vazio."""

import sqlite3
from pathlib import Path

from meu_financeiro.banco.conexao_postgres import ConexaoPostgres
from meu_financeiro.banco.esquema_banco import EsquemaBanco
from meu_financeiro.banco.repositorio_cartoes import RepositorioCartoes

CAMINHO_SQLITE = Path(__file__).resolve().parents[2] / "data" / "financeiro.db"


class ImportadorSqlite:
    def __init__(self, conexao: ConexaoPostgres | None = None, caminho_sqlite: Path | None = None):
        self._conexao = conexao or ConexaoPostgres()
        self._caminho = caminho_sqlite or CAMINHO_SQLITE
        self._esquema = EsquemaBanco()
        self._cartoes = RepositorioCartoes()

    def importar(self) -> int:
        if not self._caminho.exists():
            return 0
        with self._conexao.transacao() as conn:
            self._esquema.criar(conn)
            if self._cartoes.contar(conn) > 0:
                return 0
            origem = sqlite3.connect(self._caminho)
            origem.row_factory = sqlite3.Row
            try:
                return self._copiar(origem, conn)
            finally:
                origem.close()

    def _copiar(self, origem, destino) -> int:
        mapa_cartoes: dict[int, int] = {}
        for cartao in origem.execute("SELECT * FROM cards"):
            linha = destino.execute(
                """
                INSERT INTO cards (name, credit_limit_cents, closing_day, due_day)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (cartao["name"], cartao["credit_limit_cents"], cartao["closing_day"], cartao["due_day"]),
            ).fetchone()
            mapa_cartoes[cartao["id"]] = linha["id"]

        mapa_compras: dict[int, int] = {}
        for compra in origem.execute("SELECT * FROM purchases"):
            linha = destino.execute(
                """
                INSERT INTO purchases (card_id, description, purchase_date, total_cents, installments)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    mapa_cartoes[compra["card_id"]],
                    compra["description"],
                    compra["purchase_date"],
                    compra["total_cents"],
                    compra["installments"],
                ),
            ).fetchone()
            mapa_compras[compra["id"]] = linha["id"]

        parcelas = [
            (
                mapa_compras[item["purchase_id"]],
                item["installment_number"],
                item["invoice_month"],
                item["amount_cents"],
            )
            for item in origem.execute("SELECT * FROM invoice_items")
        ]
        for compra_id, numero, mes, centavos in parcelas:
            destino.execute(
                """
                INSERT INTO invoice_items (purchase_id, installment_number, invoice_month, amount_cents)
                VALUES (%s, %s, %s, %s)
                """,
                (compra_id, numero, mes, centavos),
            )
        return len(mapa_compras)


if __name__ == "__main__":
    quantidade = ImportadorSqlite().importar()
    print(f"Compras importadas: {quantidade}")
