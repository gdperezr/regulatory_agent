"""Grava compras e as parcelas geradas para cada fatura."""

from meu_financeiro.dominio.compra import Compra, CompraListada
from meu_financeiro.dominio.parcela_fatura import ParcelaFatura, ParcelaGravada


class RepositorioCompras:
    def inserir(self, conn, compra: Compra) -> int:
        linha = conn.execute(
            """
            INSERT INTO purchases (
              card_id, description, purchase_date, total_cents, installments
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                compra.cartao_id,
                compra.descricao,
                compra.data_compra.isoformat(),
                compra.total_centavos,
                compra.parcelas,
            ),
        ).fetchone()
        return linha["id"]

    def listar(self, conn, dono_id: int) -> list[CompraListada]:
        linhas = conn.execute(
            """
            SELECT p.id, p.card_id, c.name AS card, p.description, p.purchase_date,
                   p.total_cents, p.installments
            FROM purchases p
            JOIN cards c ON c.id = p.card_id
            WHERE c.owner_id = %s
            ORDER BY p.purchase_date DESC, p.id DESC
            """,
            (dono_id,),
        )
        return [CompraListada.da_linha(linha) for linha in linhas]

    def buscar(self, conn, dono_id: int, compra_id: int) -> CompraListada | None:
        linha = conn.execute(
            """
            SELECT p.id, p.card_id, c.name AS card, p.description, p.purchase_date,
                   p.total_cents, p.installments
            FROM purchases p
            JOIN cards c ON c.id = p.card_id
            WHERE p.id = %s AND c.owner_id = %s
            """,
            (compra_id, dono_id),
        ).fetchone()
        if linha is None:
            return None
        return CompraListada.da_linha(linha)

    def atualizar(self, conn, dono_id: int, compra_id: int, compra: Compra) -> bool:
        linha = conn.execute(
            """
            UPDATE purchases AS p
            SET card_id = %s, description = %s, purchase_date = %s,
                total_cents = %s, installments = %s
            WHERE p.id = %s
              AND EXISTS (
                SELECT 1 FROM cards c WHERE c.id = p.card_id AND c.owner_id = %s
              )
            RETURNING p.id
            """,
            (
                compra.cartao_id,
                compra.descricao,
                compra.data_compra.isoformat(),
                compra.total_centavos,
                compra.parcelas,
                compra_id,
                dono_id,
            ),
        ).fetchone()
        return linha is not None

    def remover(self, conn, dono_id: int, compra_id: int) -> bool:
        linha = conn.execute(
            """
            DELETE FROM purchases AS p
            WHERE p.id = %s
              AND EXISTS (
                SELECT 1 FROM cards c WHERE c.id = p.card_id AND c.owner_id = %s
              )
            RETURNING p.id
            """,
            (compra_id, dono_id),
        ).fetchone()
        return linha is not None

    def listar_parcelas(self, conn, compra_id: int) -> list[ParcelaGravada]:
        linhas = conn.execute(
            """
            SELECT id, installment_number, invoice_month, amount_cents
            FROM invoice_items
            WHERE purchase_id = %s
            ORDER BY installment_number
            """,
            (compra_id,),
        )
        return [
            ParcelaGravada(
                id=linha["id"],
                numero=linha["installment_number"],
                mes_fatura=linha["invoice_month"],
                valor_centavos=linha["amount_cents"],
            )
            for linha in linhas
        ]

    def atualizar_valor_parcela(self, conn, parcela_id: int, compra_id: int, valor_centavos: int) -> None:
        conn.execute(
            """
            UPDATE invoice_items
            SET amount_cents = %s
            WHERE id = %s AND purchase_id = %s
            """,
            (valor_centavos, parcela_id, compra_id),
        )

    def atualizar_parcela(
        self,
        conn,
        dono_id: int,
        parcela_id: int,
        descricao: str,
        data_compra: str,
        valor_centavos: int,
    ) -> bool:
        linha = conn.execute(
            """
            UPDATE invoice_items AS i
            SET amount_cents = %s
            FROM purchases p
            JOIN cards c ON c.id = p.card_id
            WHERE i.id = %s AND i.purchase_id = p.id AND c.owner_id = %s
            RETURNING i.purchase_id
            """,
            (valor_centavos, parcela_id, dono_id),
        ).fetchone()
        if linha is None:
            return False
        conn.execute(
            """
            UPDATE purchases
            SET description = %s,
                purchase_date = %s,
                total_cents = (
                  SELECT COALESCE(SUM(amount_cents), 0)
                  FROM invoice_items
                  WHERE purchase_id = %s
                )
            WHERE id = %s
            """,
            (descricao, data_compra, linha["purchase_id"], linha["purchase_id"]),
        )
        return True

    def remover_parcela(self, conn, dono_id: int, parcela_id: int) -> int | None:
        linha = conn.execute(
            """
            DELETE FROM invoice_items AS i
            USING purchases p, cards c
            WHERE i.id = %s
              AND i.purchase_id = p.id
              AND p.card_id = c.id
              AND c.owner_id = %s
            RETURNING i.purchase_id
            """,
            (parcela_id, dono_id),
        ).fetchone()
        if linha is None:
            return None
        compra_id = linha["purchase_id"]
        restante = conn.execute(
            "SELECT COUNT(*) AS total FROM invoice_items WHERE purchase_id = %s",
            (compra_id,),
        ).fetchone()
        if int(restante["total"]) == 0:
            conn.execute("DELETE FROM purchases WHERE id = %s", (compra_id,))
        return compra_id

    def ja_lancado(
        self,
        conn,
        cartao_id: int,
        data_compra: str,
        descricao: str,
        mes_fatura: str,
        valor_centavos: int,
        numero_parcela: int,
    ) -> bool:
        linha = conn.execute(
            """
            SELECT 1
            FROM purchases p
            JOIN invoice_items i ON i.purchase_id = p.id
            WHERE p.card_id = %s
              AND p.purchase_date = %s
              AND p.description = %s
              AND i.invoice_month = %s
              AND i.amount_cents = %s
              AND i.installment_number = %s
            LIMIT 1
            """,
            (cartao_id, data_compra, descricao, mes_fatura, valor_centavos, numero_parcela),
        ).fetchone()
        return linha is not None

    def substituir_parcelas(self, conn, compra_id: int, parcelas: list[ParcelaFatura]) -> None:
        conn.execute("DELETE FROM invoice_items WHERE purchase_id = %s", (compra_id,))
        self.inserir_parcelas(conn, compra_id, parcelas)

    def inserir_parcelas(self, conn, compra_id: int, parcelas: list[ParcelaFatura]) -> None:
        for parcela in parcelas:
            conn.execute(
                """
                INSERT INTO invoice_items (
                  purchase_id, installment_number, invoice_month, amount_cents
                ) VALUES (%s, %s, %s, %s)
                """,
                (compra_id, parcela.numero, parcela.mes_fatura, parcela.valor_centavos),
            )
