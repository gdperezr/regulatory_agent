"""Entrada no aplicativo e cadastro de outra pessoa."""

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from meu_financeiro.banco.conexao_postgres import ConexaoPostgres
from meu_financeiro.banco.repositorio_sessoes import RepositorioSessoes
from meu_financeiro.banco.repositorio_usuarios import RepositorioUsuarios
from meu_financeiro.dominio.usuario import Usuario
from meu_financeiro.excecoes_financeiras import CredenciaisInvalidas, DadosInvalidos
from meu_financeiro.servicos.hash_senha import HashSenha

_LOGIN = re.compile(r"[a-z0-9_]{3,40}")
COOKIE_LEMBRETE = "mf_lembrete"
DURACAO_LEMBRETE = timedelta(days=30)


class ServicoAutenticacao:
    def __init__(self, conexao: ConexaoPostgres | None = None, hash_senha: HashSenha | None = None):
        self._conexao = conexao or ConexaoPostgres()
        self._usuarios = RepositorioUsuarios()
        self._sessoes = RepositorioSessoes()
        self._hash = hash_senha or HashSenha()

    def preparar(self) -> None:
        """Cria a primeira pessoa a partir do ambiente, só quando o banco ainda está vazio."""
        nome = os.environ.get("ADMIN_NAME", "").strip()
        login = os.environ.get("ADMIN_LOGIN", "").strip().lower() or os.environ.get("ADMIN_EMAIL", "").strip().lower()
        senha = os.environ.get("ADMIN_PASSWORD", "")
        if not nome or not login or not senha:
            return
        try:
            self._validar(nome, login, senha)
        except DadosInvalidos:
            return
        with self._conexao.transacao() as conn:
            if self._usuarios.contar(conn) > 0:
                return
            self._usuarios.inserir(conn, nome, login, self._hash.gerar(senha))

    def entrar(self, login: str, senha: str) -> Usuario:
        with self._conexao.transacao() as conn:
            encontrado = self._usuarios.buscar_credencial(conn, login.strip().lower())
        if encontrado is None or not self._hash.confere(senha, encontrado[1]):
            raise CredenciaisInvalidas("Usuário ou senha incorretos.")
        return encontrado[0]

    def lembrar(self, usuario_id: int) -> str:
        """Cria um acesso deste aparelho por 30 dias. Devolve o token para o cookie."""
        token = secrets.token_urlsafe(32)
        with self._conexao.transacao() as conn:
            self._sessoes.limpar_expiradas(conn)
            self._sessoes.inserir(
                conn,
                usuario_id,
                self._hash_token(token),
                datetime.now(timezone.utc) + DURACAO_LEMBRETE,
            )
        return token

    def restaurar(self, token: str) -> Usuario | None:
        if not token:
            return None
        with self._conexao.transacao() as conn:
            linha = self._sessoes.buscar_usuario(conn, self._hash_token(token))
        if linha is None:
            return None
        return Usuario.da_linha(linha)

    def esquecer(self, token: str) -> None:
        if not token:
            return
        with self._conexao.transacao() as conn:
            self._sessoes.remover(conn, self._hash_token(token))

    def listar(self) -> list[Usuario]:
        with self._conexao.transacao() as conn:
            return self._usuarios.listar(conn)

    def cadastrar(self, nome: str, login: str, senha: str) -> None:
        self._validar(nome, login, senha)
        with self._conexao.transacao() as conn:
            self._usuarios.inserir(conn, nome.strip(), login.strip().lower(), self._hash.gerar(senha))

    def _validar(self, nome: str, login: str, senha: str) -> None:
        if not nome.strip():
            raise DadosInvalidos("Informe o nome.")
        if not _LOGIN.fullmatch(login.strip().lower()):
            raise DadosInvalidos("O usuário deve ter de 3 a 40 caracteres: letras minúsculas, números e _.")
        if len(senha) < 8:
            raise DadosInvalidos("A senha precisa ter pelo menos 8 caracteres.")

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
