"""Consulta totais e linhas das faturas já calculadas."""

from meu_financeiro.dominio.detalhe_fatura import DetalheFatura
from meu_financeiro.dominio.resumo_fatura import ResumoFatura


class RepositorioFaturas:
    def resumir(self, conn, dono_id: int) -> list[ResumoFatura]:
        linhas = conn.execute(
            """
            SELECT i.invoice_month, c.name AS card, SUM(i.amount_cents) AS amount_cents
            FROM invoice_items i
            JOIN purchases p ON p.id = i.purchase_id
            JOIN cards c ON c.id = p.card_id
            WHERE c.owner_id = %s
            GROUP BY i.invoice_month, c.id, c.name
            ORDER BY i.invoice_month, c.name
            """,
            (dono_id,),
        )
        return [ResumoFatura.da_linha(linha) for linha in linhas]

    def detalhar(self, conn, dono_id: int, mes_fatura: str) -> list[DetalheFatura]:
        linhas = conn.execute(
            """
            SELECT i.id AS item_id, p.id AS purchase_id, c.name AS card, p.description,
                   p.purchase_date, i.installment_number, p.installments, i.amount_cents
            FROM invoice_items i
            JOIN purchases p ON p.id = i.purchase_id
            JOIN cards c ON c.id = p.card_id
            WHERE i.invoice_month = %s AND c.owner_id = %s
            ORDER BY c.name, p.purchase_date, p.id
            """,
            (mes_fatura, dono_id),
        )
        return [DetalheFatura.da_linha(linha) for linha in linhas]

    def total_do_mes(self, conn, dono_id: int, mes_fatura: str) -> int:
        linha = conn.execute(
            """
            SELECT COALESCE(SUM(i.amount_cents), 0) AS total
            FROM invoice_items i
            JOIN purchases p ON p.id = i.purchase_id
            JOIN cards c ON c.id = p.card_id
            WHERE c.owner_id = %s AND i.invoice_month = %s
            """,
            (dono_id, mes_fatura),
        ).fetchone()
        return int(linha["total"])
