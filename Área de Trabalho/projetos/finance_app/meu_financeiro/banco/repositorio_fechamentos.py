"""Guarda o resultado fechado de cada mês."""

from datetime import datetime

from meu_financeiro.dominio.fechamento_mensal import FechamentoMensal


class RepositorioFechamentos:
    def salvar(self, conn, dono_id: int, fechamento: FechamentoMensal) -> None:
        conn.execute(
            """
            INSERT INTO month_closings (
              owner_id, closing_month, income_cents, expense_cents, balance_cents, closed_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_id, closing_month) DO UPDATE SET
              income_cents = EXCLUDED.income_cents,
              expense_cents = EXCLUDED.expense_cents,
              balance_cents = EXCLUDED.balance_cents,
              closed_at = EXCLUDED.closed_at
            """,
            (
                dono_id,
                fechamento.mes,
                fechamento.receitas_centavos,
                fechamento.despesas_centavos,
                fechamento.saldo_centavos,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    def buscar(self, conn, dono_id: int, mes: str) -> FechamentoMensal | None:
        linha = conn.execute(
            """
            SELECT closing_month, income_cents, expense_cents, balance_cents
            FROM month_closings
            WHERE owner_id = %s AND closing_month = %s
            """,
            (dono_id, mes),
        ).fetchone()
        if linha is None:
            return None
        return FechamentoMensal.da_linha(linha)

    def listar(self, conn, dono_id: int) -> list[FechamentoMensal]:
        linhas = conn.execute(
            """
            SELECT closing_month, income_cents, expense_cents, balance_cents
            FROM month_closings
            WHERE owner_id = %s
            ORDER BY closing_month DESC
            """,
            (dono_id,),
        ).fetchall()
        return [FechamentoMensal.da_linha(linha) for linha in linhas]
