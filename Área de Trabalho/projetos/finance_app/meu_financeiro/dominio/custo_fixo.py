"""Gasto que se repete todo mês, como aluguel ou internet."""

from dataclasses import dataclass

from meu_financeiro.excecoes_financeiras import DadosInvalidos


@dataclass(frozen=True)
class CustoFixo:
    id: int | None
    descricao: str
    valor_centavos: int

    @classmethod
    def novo(cls, descricao: str, valor_reais: float) -> "CustoFixo":
        descricao_limpa = descricao.strip()
        if not descricao_limpa:
            raise DadosInvalidos("Informe a descrição do custo fixo.")
        centavos = round(valor_reais * 100)
        if centavos <= 0:
            raise DadosInvalidos("O valor do custo fixo deve ser positivo.")
        return cls(id=None, descricao=descricao_limpa, valor_centavos=centavos)

    @classmethod
    def da_linha(cls, linha) -> "CustoFixo":
        return cls(id=linha["id"], descricao=linha["description"], valor_centavos=linha["amount_cents"])
