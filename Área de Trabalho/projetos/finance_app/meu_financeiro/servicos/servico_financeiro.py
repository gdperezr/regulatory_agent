"""Ponto único usado pela interface para cartões, compras e faturas."""

from datetime import date

from meu_financeiro.banco.conexao_postgres import ConexaoPostgres
from meu_financeiro.banco.esquema_banco import EsquemaBanco
from meu_financeiro.banco.repositorio_cartoes import RepositorioCartoes
from meu_financeiro.banco.repositorio_compras import RepositorioCompras
from meu_financeiro.banco.repositorio_faturas import RepositorioFaturas
from meu_financeiro.dominio.cartao import Cartao
from meu_financeiro.dominio.compra import Compra, CompraListada
from meu_financeiro.dominio.detalhe_fatura import DetalheFatura
from meu_financeiro.dominio.lancamento_fatura import LancamentoFatura
from meu_financeiro.dominio.leitura_fatura import LeituraFatura
from meu_financeiro.dominio.parcela_fatura import ParcelaFatura, ParcelaGravada
from meu_financeiro.dominio.resumo_fatura import ResumoFatura
from meu_financeiro.excecoes_financeiras import CartaoNaoEncontrado, DadosInvalidos
from meu_financeiro.servicos.calculadora_parcelas import CalculadoraParcelas
from meu_financeiro.servicos.leitor_fatura import LeitorFatura


class ServicoFinanceiro:
    def __init__(
        self,
        conexao: ConexaoPostgres | None = None,
        calculadora: CalculadoraParcelas | None = None,
    ):
        self._conexao = conexao or ConexaoPostgres()
        self._calculadora = calculadora or CalculadoraParcelas()
        self._esquema = EsquemaBanco()
        self._cartoes = RepositorioCartoes()
        self._compras = RepositorioCompras()
        self._faturas = RepositorioFaturas()
        self._leitor = LeitorFatura()

    def inicializar(self) -> None:
        with self._conexao.transacao() as conn:
            self._esquema.criar(conn)

    def cadastrar_cartao(
        self,
        usuario_id: int,
        nome: str,
        limite_reais: float,
        dia_fechamento: int,
        dia_vencimento: int,
    ) -> None:
        cartao = Cartao.novo(nome, limite_reais, dia_fechamento, dia_vencimento)
        with self._conexao.transacao() as conn:
            self._cartoes.inserir(conn, usuario_id, cartao)

    def listar_cartoes(self, usuario_id: int) -> list[Cartao]:
        with self._conexao.transacao() as conn:
            return self._cartoes.listar(conn, usuario_id)

    def atualizar_cartao(
        self,
        usuario_id: int,
        cartao_id: int,
        nome: str,
        limite_reais: float,
        dia_fechamento: int,
        dia_vencimento: int,
    ) -> None:
        cartao = Cartao.novo(nome, limite_reais, dia_fechamento, dia_vencimento)
        with self._conexao.transacao() as conn:
            if not self._cartoes.atualizar(conn, usuario_id, cartao_id, cartao):
                raise CartaoNaoEncontrado("Cartão não encontrado.")

    def remover_cartao(self, usuario_id: int, cartao_id: int) -> None:
        with self._conexao.transacao() as conn:
            if self._cartoes.buscar_por_id(conn, usuario_id, cartao_id) is None:
                raise CartaoNaoEncontrado("Cartão não encontrado.")
            if self._cartoes.tem_compras(conn, cartao_id):
                raise DadosInvalidos("Apague as compras deste cartão antes de excluí-lo.")
            self._cartoes.remover(conn, usuario_id, cartao_id)

    def cadastrar_compra(
        self,
        usuario_id: int,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total_reais: float,
        parcelas: int,
    ) -> None:
        with self._conexao.transacao() as conn:
            cartao = self._cartoes.buscar_por_id(conn, usuario_id, cartao_id)
            if cartao is None:
                raise CartaoNaoEncontrado("Cartão não encontrado.")
            compra = Compra.nova(cartao_id, descricao, data_compra, total_reais, parcelas)
            compra_id = self._compras.inserir(conn, compra)
            parcelas_fatura = self._calculadora.distribuir(
                compra.data_compra,
                cartao.dia_fechamento,
                compra.total_centavos,
                compra.parcelas,
            )
            self._compras.inserir_parcelas(conn, compra_id, parcelas_fatura)

    def listar_compras(self, usuario_id: int) -> list[CompraListada]:
        with self._conexao.transacao() as conn:
            return self._compras.listar(conn, usuario_id)

    def atualizar_compra(
        self,
        usuario_id: int,
        compra_id: int,
        cartao_id: int,
        descricao: str,
        data_compra: date,
        total_reais: float,
        parcelas: int,
    ) -> None:
        with self._conexao.transacao() as conn:
            existente = self._compras.buscar(conn, usuario_id, compra_id)
            if existente is None:
                raise DadosInvalidos("Compra não encontrada.")
            cartao = self._cartoes.buscar_por_id(conn, usuario_id, cartao_id)
            if cartao is None:
                raise CartaoNaoEncontrado("Cartão não encontrado.")
            cartao_antigo = self._cartoes.buscar_por_id(conn, usuario_id, existente.cartao_id)
            itens = self._compras.listar_parcelas(conn, compra_id)
            compra = Compra.nova(cartao_id, descricao, data_compra, total_reais, parcelas)
            if not self._compras.atualizar(conn, usuario_id, compra_id, compra):
                raise DadosInvalidos("Compra não encontrada.")
            if cartao_antigo is not None and self._manter_linha_de_fatura(existente, cartao_antigo, itens):
                self._compras.atualizar_valor_parcela(conn, itens[0].id, compra_id, compra.total_centavos)
                return
            novas = self._calculadora.distribuir(
                compra.data_compra,
                cartao.dia_fechamento,
                compra.total_centavos,
                compra.parcelas,
            )
            self._compras.substituir_parcelas(conn, compra_id, novas)

    def remover_compra(self, usuario_id: int, compra_id: int) -> None:
        with self._conexao.transacao() as conn:
            if not self._compras.remover(conn, usuario_id, compra_id):
                raise DadosInvalidos("Compra não encontrada.")

    def atualizar_parcela(
        self,
        usuario_id: int,
        parcela_id: int,
        descricao: str,
        data_compra: date,
        valor_reais: float,
    ) -> None:
        descricao_limpa = descricao.strip()
        if not descricao_limpa:
            raise DadosInvalidos("Informe a descrição.")
        if not isinstance(data_compra, date):
            raise DadosInvalidos("Informe a data da compra.")
        centavos = round(valor_reais * 100)
        if centavos <= 0:
            raise DadosInvalidos("O valor deve ser positivo.")
        with self._conexao.transacao() as conn:
            if not self._compras.atualizar_parcela(
                conn,
                usuario_id,
                parcela_id,
                descricao_limpa,
                data_compra.isoformat(),
                centavos,
            ):
                raise DadosInvalidos("Parcela não encontrada.")

    def remover_parcela(self, usuario_id: int, parcela_id: int) -> None:
        with self._conexao.transacao() as conn:
            if self._compras.remover_parcela(conn, usuario_id, parcela_id) is None:
                raise DadosInvalidos("Parcela não encontrada.")

    def ler_fatura(self, conteudo: bytes, mes_fatura: str) -> LeituraFatura:
        return self._leitor.ler(conteudo, mes_fatura)

    def importar_lancamentos_fatura(
        self,
        usuario_id: int,
        cartao_id: int,
        mes_fatura: str,
        lancamentos: list[LancamentoFatura],
    ) -> tuple[int, int]:
        if not lancamentos:
            raise DadosInvalidos("Selecione ao menos uma despesa da fatura.")
        inseridos = 0
        repetidos = 0
        with self._conexao.transacao() as conn:
            cartao = self._cartoes.buscar_por_id(conn, usuario_id, cartao_id)
            if cartao is None:
                raise CartaoNaoEncontrado("Cartão não encontrado.")
            for item in lancamentos:
                if self._compras.ja_lancado(
                    conn,
                    cartao_id,
                    item.data.isoformat(),
                    item.descricao,
                    mes_fatura,
                    item.valor_centavos,
                    item.numero_parcela,
                ):
                    repetidos += 1
                    continue
                compra = Compra.com_centavos(
                    cartao_id,
                    item.descricao,
                    item.data,
                    item.valor_centavos,
                    item.total_parcelas,
                )
                compra_id = self._compras.inserir(conn, compra)
                self._compras.inserir_parcelas(
                    conn,
                    compra_id,
                    [
                        ParcelaFatura(
                            numero=item.numero_parcela,
                            mes_fatura=mes_fatura,
                            valor_centavos=item.valor_centavos,
                        )
                    ],
                )
                inseridos += 1
        return inseridos, repetidos

    def resumir_faturas(self, usuario_id: int) -> list[ResumoFatura]:
        with self._conexao.transacao() as conn:
            return self._faturas.resumir(conn, usuario_id)

    def detalhar_fatura(self, usuario_id: int, mes_fatura: str) -> list[DetalheFatura]:
        with self._conexao.transacao() as conn:
            return self._faturas.detalhar(conn, usuario_id, mes_fatura)

    def _manter_linha_de_fatura(self, compra: CompraListada, cartao: Cartao, itens: list[ParcelaGravada]) -> bool:
        """Linha importada da fatura fica no mês escolhido, sem gerar as outras parcelas."""
        if len(itens) != 1:
            return False
        if compra.parcelas > 1:
            return True
        prevista = self._calculadora.distribuir(
            compra.data_compra,
            cartao.dia_fechamento,
            compra.total_centavos,
            1,
        )[0]
        unica = itens[0]
        return unica.numero != prevista.numero or unica.mes_fatura != prevista.mes_fatura
