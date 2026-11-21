"""O que o leitor conseguiu tirar de um PDF de fatura."""

from dataclasses import dataclass

from meu_financeiro.dominio.lancamento_fatura import LancamentoFatura


@dataclass(frozen=True)
class LeituraFatura:
    banco: str
    lancamentos: list[LancamentoFatura]
    ignorados: list[str]
    avisos: list[str]
