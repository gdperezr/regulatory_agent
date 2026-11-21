"""Distribui o valor de uma compra nas faturas mensais."""

import calendar
from datetime import date

from meu_financeiro.dominio.parcela_fatura import ParcelaFatura


class CalculadoraParcelas:
    """O mês da fatura é o mês de fechamento, não o mês de vencimento.

    Compra no dia do fechamento ou depois entra na fatura do mês seguinte.
    Dia 29, 30 ou 31 acompanha o último dia dos meses mais curtos.
    O resto da divisão em centavos vai para as primeiras parcelas.
    """

    def distribuir(
        self,
        data_compra: date,
        dia_fechamento: int,
        total_centavos: int,
        parcelas: int,
    ) -> list[ParcelaFatura]:
        ano, mes = self.mes_inicial(data_compra, dia_fechamento)
        base, resto = divmod(total_centavos, parcelas)
        resultado = []
        for indice in range(parcelas):
            ano_parcela, mes_parcela = self.somar_meses(ano, mes, indice)
            centavos = base + (1 if indice < resto else 0)
            resultado.append(
                ParcelaFatura(
                    numero=indice + 1,
                    mes_fatura=f"{ano_parcela:04d}-{mes_parcela:02d}",
                    valor_centavos=centavos,
                )
            )
        return resultado

    def mes_inicial(self, data_compra: date, dia_fechamento: int) -> tuple[int, int]:
        ultimo_dia = calendar.monthrange(data_compra.year, data_compra.month)[1]
        fechamento = min(dia_fechamento, ultimo_dia)
        deslocamento = 1 if data_compra.day >= fechamento else 0
        return self.somar_meses(data_compra.year, data_compra.month, deslocamento)

    def somar_meses(self, ano: int, mes: int, deslocamento: int) -> tuple[int, int]:
        indice = ano * 12 + mes - 1 + deslocamento
        return indice // 12, indice % 12 + 1
