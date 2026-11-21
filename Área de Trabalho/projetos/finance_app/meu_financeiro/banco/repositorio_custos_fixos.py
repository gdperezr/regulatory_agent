"""Grava e lê os custos fixos de cada pessoa."""

from meu_financeiro.dominio.custo_fixo import CustoFixo


class RepositorioCustosFixos:
    def inserir(self, conn, dono_id: int, custo: CustoFixo) -> int:
        linha = conn.execute(
            """
            INSERT INTO fixed_costs (owner_id, description, amount_cents)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (dono_id, custo.descricao, custo.valor_centavos),
        ).fetchone()
        return linha["id"]

    def listar(self, conn, dono_id: int) -> list[CustoFixo]:
        linhas = conn.execute(
            """
            SELECT id, description, amount_cents
            FROM fixed_costs
            WHERE owner_id = %s
            ORDER BY description, id
            """,
            (dono_id,),
        )
        return [CustoFixo.da_linha(linha) for linha in linhas]

    def atualizar(self, conn, dono_id: int, custo_id: int, custo: CustoFixo) -> bool:
        linha = conn.execute(
            """
            UPDATE fixed_costs
            SET description = %s, amount_cents = %s
            WHERE id = %s AND owner_id = %s
            RETURNING id
            """,
            (custo.descricao, custo.valor_centavos, custo_id, dono_id),
        ).fetchone()
        return linha is not None

    def remover(self, conn, dono_id: int, custo_id: int) -> None:
        conn.execute(
            "DELETE FROM fixed_costs WHERE id = %s AND owner_id = %s",
            (custo_id, dono_id),
        )
