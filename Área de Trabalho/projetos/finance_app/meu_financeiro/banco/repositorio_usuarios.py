"""Grava e lê as pessoas que podem entrar no aplicativo."""

from psycopg.errors import UniqueViolation

from meu_financeiro.dominio.usuario import Usuario
from meu_financeiro.excecoes_financeiras import DadosInvalidos


class RepositorioUsuarios:
    def inserir(self, conn, nome: str, login: str, senha_hash: str) -> Usuario:
        try:
            linha = conn.execute(
                """
                INSERT INTO users (name, login, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, name, login
                """,
                (nome, login, senha_hash),
            ).fetchone()
        except UniqueViolation as erro:
            raise DadosInvalidos("Já existe uma pessoa com esse usuário.") from erro
        return Usuario.da_linha(linha)

    def listar(self, conn) -> list[Usuario]:
        linhas = conn.execute("SELECT id, name, login FROM users ORDER BY name")
        return [Usuario.da_linha(linha) for linha in linhas]

    def contar(self, conn) -> int:
        linha = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(linha["total"])

    def buscar_credencial(self, conn, login: str) -> tuple[Usuario, str] | None:
        linha = conn.execute(
            "SELECT id, name, login, password_hash FROM users WHERE login = %s",
            (login,),
        ).fetchone()
        if linha is None:
            return None
        return Usuario.da_linha(linha), linha["password_hash"]
