"""Cartão de crédito cadastrado pelo usuário."""

from dataclasses import dataclass

from meu_financeiro.excecoes_financeiras import DadosInvalidos


@dataclass(frozen=True)
class Cartao:
    """Nome, limite e dias de fechamento e vencimento.

    O limite fica em centavos para evitar erro de arredondamento.
    """

    id: int | None
    nome: str
    limite_centavos: int
    dia_fechamento: int
    dia_vencimento: int

    @classmethod
    def novo(
        cls,
        nome: str,
        limite_reais: float,
        dia_fechamento: int,
        dia_vencimento: int,
    ) -> "Cartao":
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise DadosInvalidos("Informe o nome do cartão.")
        if not 1 <= int(dia_fechamento) <= 31:
            raise DadosInvalidos("O dia de fechamento deve ficar entre 1 e 31.")
        if not 1 <= int(dia_vencimento) <= 31:
            raise DadosInvalidos("O dia de vencimento deve ficar entre 1 e 31.")
        limite_centavos = round(limite_reais * 100)
        if limite_centavos < 0:
            raise DadosInvalidos("O limite não pode ser negativo.")
        return cls(
            id=None,
            nome=nome_limpo,
            limite_centavos=limite_centavos,
            dia_fechamento=int(dia_fechamento),
            dia_vencimento=int(dia_vencimento),
        )

    @classmethod
    def da_linha(cls, linha) -> "Cartao":
        return cls(
            id=linha["id"],
            nome=linha["name"],
            limite_centavos=linha["credit_limit_cents"],
            dia_fechamento=linha["closing_day"],
            dia_vencimento=linha["due_day"],
        )
