"""Compra lançada em um cartão, à vista ou parcelada."""

from dataclasses import dataclass
from datetime import date

from meu_financeiro.excecoes_financeiras import DadosInvalidos


@dataclass(frozen=True)
class Compra:
    """Valor total em centavos e quantidade de parcelas."""

    id: int | None
    cartao_id: int
    descricao: str
    data_compra: date
    total_centavos: int
    parcelas: int

    @classmethod
    def nova(
        cls,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total_reais: float,
        parcelas: int,
    ) -> "Compra":
        descricao_limpa = descricao.strip()
        if not descricao_limpa:
            raise DadosInvalidos("Informe a descrição.")
        if not isinstance(data_compra, date):
            raise DadosInvalidos("Informe a data da compra.")
        total_centavos = round(total_reais * 100)
        if total_centavos <= 0:
            raise DadosInvalidos("O valor deve ser positivo.")
        quantidade = int(parcelas)
        if not 1 <= quantidade <= 120:
            raise DadosInvalidos("O número de parcelas deve ficar entre 1 e 120.")
        return cls(
            id=None,
            cartao_id=int(cartao_id),
            descricao=descricao_limpa,
            data_compra=data_compra,
            total_centavos=total_centavos,
            parcelas=quantidade,
        )

    @classmethod
    def com_centavos(
        cls,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total_centavos: int,
        parcelas: int,
    ) -> "Compra":
        descricao_limpa = descricao.strip()
        if not descricao_limpa:
            raise DadosInvalidos("Informe a descrição.")
        if not isinstance(data_compra, date):
            raise DadosInvalidos("Informe a data da compra.")
        if int(total_centavos) <= 0:
            raise DadosInvalidos("O valor deve ser positivo.")
        quantidade = int(parcelas)
        if not 1 <= quantidade <= 120:
            raise DadosInvalidos("O número de parcelas deve ficar entre 1 e 120.")
        return cls(
            id=None,
            cartao_id=int(cartao_id),
            descricao=descricao_limpa,
            data_compra=data_compra,
            total_centavos=int(total_centavos),
            parcelas=quantidade,
        )


@dataclass(frozen=True)
class CompraListada:
    """Compra de uma pessoa, com o nome do cartão, para a lista da tela."""

    id: int
    cartao_id: int
    cartao: str
    descricao: str
    data_compra: date
    total_centavos: int
    parcelas: int

    @classmethod
    def da_linha(cls, linha) -> "CompraListada":
        bruta = linha["purchase_date"]
        data = bruta if isinstance(bruta, date) else date.fromisoformat(str(bruta))
        return cls(
            id=linha["id"],
            cartao_id=linha["card_id"],
            cartao=linha["card"],
            descricao=linha["description"],
            data_compra=data,
            total_centavos=linha["total_cents"],
            parcelas=linha["installments"],
        )
