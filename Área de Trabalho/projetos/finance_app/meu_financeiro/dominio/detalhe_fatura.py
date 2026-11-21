"""Linha de uma fatura: compra, parcela e valor."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetalheFatura:
    cartao: str
    descricao: str
    data_compra: str
    numero_parcela: int
    total_parcelas: int
    valor_centavos: int
    item_id: int
    compra_id: int

    @classmethod
    def da_linha(cls, linha) -> "DetalheFatura":
        return cls(
            cartao=linha["card"],
            descricao=linha["description"],
            data_compra=str(linha["purchase_date"]),
            numero_parcela=linha["installment_number"],
            total_parcelas=linha["installments"],
            valor_centavos=linha["amount_cents"],
            item_id=linha["item_id"],
            compra_id=linha["purchase_id"],
        )
