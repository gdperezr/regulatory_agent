"""Grava o lembrete de entrada deste aparelho. A senha não fica aqui."""


class RepositorioSessoes:
    def inserir(self, conn, usuario_id: int, token_hash: str, expira_em) -> None:
        conn.execute(
            """
            INSERT INTO remembered_sessions (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (usuario_id, token_hash, expira_em),
        )

    def buscar_usuario(self, conn, token_hash: str):
        return conn.execute(
            """
            SELECT u.id, u.name, u.login
            FROM remembered_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > NOW()
            """,
            (token_hash,),
        ).fetchone()

    def remover(self, conn, token_hash: str) -> None:
        conn.execute(
            "DELETE FROM remembered_sessions WHERE token_hash = %s",
            (token_hash,),
        )

    def limpar_expiradas(self, conn) -> None:
        conn.execute("DELETE FROM remembered_sessions WHERE expires_at <= NOW()")
