"""Custos fixos, recebimentos e o fechamento do mês de uma pessoa."""

from meu_financeiro.banco.conexao_postgres import ConexaoPostgres
from meu_financeiro.banco.repositorio_custos_fixos import RepositorioCustosFixos
from meu_financeiro.banco.repositorio_faturas import RepositorioFaturas
from meu_financeiro.banco.repositorio_fechamentos import RepositorioFechamentos
from meu_financeiro.banco.repositorio_recebimentos import RepositorioRecebimentos
from meu_financeiro.dominio.custo_fixo import CustoFixo
from meu_financeiro.dominio.despesas_do_mes import DespesasDoMes
from meu_financeiro.dominio.fechamento_mensal import FechamentoMensal
from meu_financeiro.dominio.recebimento import Recebimento
from meu_financeiro.excecoes_financeiras import DadosInvalidos
from meu_financeiro.servicos.exportar_fechamentos import gerar_xlsx


class ServicoFechamento:
    def __init__(self, conexao: ConexaoPostgres | None = None):
        self._conexao = conexao or ConexaoPostgres()
        self._custos = RepositorioCustosFixos()
        self._recebimentos = RepositorioRecebimentos()
        self._faturas = RepositorioFaturas()
        self._fechamentos = RepositorioFechamentos()

    def cadastrar_custo_fixo(self, usuario_id: int, descricao: str, valor_reais: float) -> None:
        custo = CustoFixo.novo(descricao, valor_reais)
        with self._conexao.transacao() as conn:
            self._custos.inserir(conn, usuario_id, custo)

    def listar_custos_fixos(self, usuario_id: int) -> list[CustoFixo]:
        with self._conexao.transacao() as conn:
            return self._custos.listar(conn, usuario_id)

    def atualizar_custo_fixo(self, usuario_id: int, custo_id: int, descricao: str, valor_reais: float) -> None:
        custo = CustoFixo.novo(descricao, valor_reais)
        with self._conexao.transacao() as conn:
            if not self._custos.atualizar(conn, usuario_id, custo_id, custo):
                raise DadosInvalidos("Custo fixo não encontrado.")

    def remover_custo_fixo(self, usuario_id: int, custo_id: int) -> None:
        with self._conexao.transacao() as conn:
            self._custos.remover(conn, usuario_id, custo_id)

    def cadastrar_recebimento(self, usuario_id: int, descricao: str, valor_reais: float, mes: str) -> None:
        recebimento = Recebimento.novo(descricao, valor_reais, mes)
        with self._conexao.transacao() as conn:
            self._recebimentos.inserir(conn, usuario_id, recebimento)

    def listar_recebimentos(self, usuario_id: int, mes: str) -> list[Recebimento]:
        with self._conexao.transacao() as conn:
            return self._recebimentos.listar(conn, usuario_id, mes)

    def atualizar_recebimento(
        self,
        usuario_id: int,
        recebimento_id: int,
        descricao: str,
        valor_reais: float,
        mes: str,
    ) -> None:
        recebimento = Recebimento.novo(descricao, valor_reais, mes)
        with self._conexao.transacao() as conn:
            if not self._recebimentos.atualizar(conn, usuario_id, recebimento_id, recebimento):
                raise DadosInvalidos("Recebimento não encontrado.")

    def remover_recebimento(self, usuario_id: int, recebimento_id: int) -> None:
        with self._conexao.transacao() as conn:
            self._recebimentos.remover(conn, usuario_id, recebimento_id)

    def despesas_do_mes(self, usuario_id: int, mes: str) -> DespesasDoMes:
        with self._conexao.transacao() as conn:
            return DespesasDoMes(
                mes=mes,
                faturas=self._faturas.detalhar(conn, usuario_id, mes),
                custos_fixos=self._custos.listar(conn, usuario_id),
            )

    def fechar_mes(self, usuario_id: int, mes: str) -> FechamentoMensal:
        with self._conexao.transacao() as conn:
            faturas = self._faturas.total_do_mes(conn, usuario_id, mes)
            custos = sum(custo.valor_centavos for custo in self._custos.listar(conn, usuario_id))
            receitas = sum(item.valor_centavos for item in self._recebimentos.listar(conn, usuario_id, mes))
            fechamento = FechamentoMensal.calcular(mes, receitas, faturas + custos)
            self._fechamentos.salvar(conn, usuario_id, fechamento)
            return fechamento

    def listar_fechamentos(self, usuario_id: int) -> list[FechamentoMensal]:
        with self._conexao.transacao() as conn:
            return self._fechamentos.listar(conn, usuario_id)

    def exportar_fechamentos_xlsx(self, usuario_id: int) -> bytes:
        with self._conexao.transacao() as conn:
            fechamentos = self._fechamentos.listar(conn, usuario_id)
            detalhes = {
                item.mes: (
                    self._recebimentos.listar(conn, usuario_id, item.mes),
                    DespesasDoMes(
                        mes=item.mes,
                        faturas=self._faturas.detalhar(conn, usuario_id, item.mes),
                        custos_fixos=self._custos.listar(conn, usuario_id),
                    ),
                )
                for item in fechamentos
            }
        return gerar_xlsx(fechamentos, detalhes)
