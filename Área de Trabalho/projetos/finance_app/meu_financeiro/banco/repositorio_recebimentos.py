"""Grava e lê os recebimentos de cada pessoa, por mês."""

from meu_financeiro.dominio.recebimento import Recebimento


class RepositorioRecebimentos:
    def inserir(self, conn, dono_id: int, recebimento: Recebimento) -> int:
        linha = conn.execute(
            """
            INSERT INTO incomes (owner_id, description, amount_cents, income_month)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (dono_id, recebimento.descricao, recebimento.valor_centavos, recebimento.mes),
        ).fetchone()
        return linha["id"]

    def listar(self, conn, dono_id: int, mes: str) -> list[Recebimento]:
        linhas = conn.execute(
            """
            SELECT id, description, amount_cents, income_month
            FROM incomes
            WHERE owner_id = %s AND income_month = %s
            ORDER BY description, id
            """,
            (dono_id, mes),
        )
        return [Recebimento.da_linha(linha) for linha in linhas]

    def atualizar(self, conn, dono_id: int, recebimento_id: int, recebimento: Recebimento) -> bool:
        linha = conn.execute(
            """
            UPDATE incomes
            SET description = %s, amount_cents = %s, income_month = %s
            WHERE id = %s AND owner_id = %s
            RETURNING id
            """,
            (
                recebimento.descricao,
                recebimento.valor_centavos,
                recebimento.mes,
                recebimento_id,
                dono_id,
            ),
        ).fetchone()
        return linha is not None

    def remover(self, conn, dono_id: int, recebimento_id: int) -> None:
        conn.execute(
            "DELETE FROM incomes WHERE id = %s AND owner_id = %s",
            (recebimento_id, dono_id),
        )
