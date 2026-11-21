"""Erros de negócio do Meu Financeiro."""


class ErroFinanceiro(Exception):
    """Base dos erros que a interface pode mostrar ao usuário."""


class DadosInvalidos(ErroFinanceiro):
    """Dados de cartão ou compra que não passam na validação."""


class CartaoDuplicado(ErroFinanceiro):
    """Já existe um cartão com o mesmo nome."""


class CartaoNaoEncontrado(ErroFinanceiro):
    """O cartão informado não está no banco."""


class CredenciaisInvalidas(ErroFinanceiro):
    """E-mail ou senha não conferem."""


class ConfiguracaoAusente(ErroFinanceiro):
    """Falta a conexão com o PostgreSQL."""


class FaturaNaoLida(ErroFinanceiro):
    """O PDF da fatura não pôde ser interpretado."""
