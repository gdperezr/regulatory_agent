"""Dinheiro que entrou em um mês, como salário ou extra."""

from dataclasses import dataclass

from meu_financeiro.excecoes_financeiras import DadosInvalidos


@dataclass(frozen=True)
class Recebimento:
    id: int | None
    descricao: str
    mes: str
    valor_centavos: int

    @classmethod
    def novo(cls, descricao: str, valor_reais: float, mes: str) -> "Recebimento":
        descricao_limpa = descricao.strip()
        if not descricao_limpa:
            raise DadosInvalidos("Informe a descrição do recebimento.")
        centavos = round(valor_reais * 100)
        if centavos <= 0:
            raise DadosInvalidos("O valor do recebimento deve ser positivo.")
        if len(mes) != 7 or mes[4] != "-":
            raise DadosInvalidos("Informe o mês do recebimento.")
        return cls(id=None, descricao=descricao_limpa, mes=mes, valor_centavos=centavos)

    @classmethod
    def da_linha(cls, linha) -> "Recebimento":
        return cls(
            id=linha["id"],
            descricao=linha["description"],
            mes=linha["income_month"],
            valor_centavos=linha["amount_cents"],
        )
