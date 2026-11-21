"""Grava e lê cartões na tabela cards."""

from psycopg.errors import UniqueViolation

from meu_financeiro.dominio.cartao import Cartao
from meu_financeiro.excecoes_financeiras import CartaoDuplicado


class RepositorioCartoes:
    def inserir(self, conn, dono_id: int, cartao: Cartao) -> int:
        try:
            linha = conn.execute(
                """
                INSERT INTO cards (owner_id, name, credit_limit_cents, closing_day, due_day)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    dono_id,
                    cartao.nome,
                    cartao.limite_centavos,
                    cartao.dia_fechamento,
                    cartao.dia_vencimento,
                ),
            ).fetchone()
        except UniqueViolation as erro:
            raise CartaoDuplicado("Você já tem um cartão com esse nome.") from erro
        return linha["id"]

    def listar(self, conn, dono_id: int) -> list[Cartao]:
        linhas = conn.execute(
            "SELECT * FROM cards WHERE owner_id = %s ORDER BY name",
            (dono_id,),
        )
        return [Cartao.da_linha(linha) for linha in linhas]

    def buscar_por_id(self, conn, dono_id: int, cartao_id: int) -> Cartao | None:
        linha = conn.execute(
            "SELECT * FROM cards WHERE id = %s AND owner_id = %s",
            (cartao_id, dono_id),
        ).fetchone()
        if linha is None:
            return None
        return Cartao.da_linha(linha)

    def atualizar(self, conn, dono_id: int, cartao_id: int, cartao: Cartao) -> bool:
        try:
            linha = conn.execute(
                """
                UPDATE cards
                SET name = %s, credit_limit_cents = %s, closing_day = %s, due_day = %s
                WHERE id = %s AND owner_id = %s
                RETURNING id
                """,
                (
                    cartao.nome,
                    cartao.limite_centavos,
                    cartao.dia_fechamento,
                    cartao.dia_vencimento,
                    cartao_id,
                    dono_id,
                ),
            ).fetchone()
        except UniqueViolation as erro:
            raise CartaoDuplicado("Você já tem um cartão com esse nome.") from erro
        return linha is not None

    def tem_compras(self, conn, cartao_id: int) -> bool:
        linha = conn.execute(
            "SELECT 1 FROM purchases WHERE card_id = %s LIMIT 1",
            (cartao_id,),
        ).fetchone()
        return linha is not None

    def remover(self, conn, dono_id: int, cartao_id: int) -> bool:
        linha = conn.execute(
            "DELETE FROM cards WHERE id = %s AND owner_id = %s RETURNING id",
            (cartao_id, dono_id),
        ).fetchone()
        return linha is not None

    def contar(self, conn) -> int:
        linha = conn.execute("SELECT COUNT(*) AS total FROM cards").fetchone()
        return int(linha["total"])
