"""Gera e confere o hash da senha. A senha em claro não fica no banco."""

import hashlib
import secrets


class HashSenha:
    _ITERACOES = 200_000

    def gerar(self, senha: str) -> str:
        sal = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, self._ITERACOES)
        return f"pbkdf2${self._ITERACOES}${sal.hex()}${digest.hex()}"

    def confere(self, senha: str, armazenado: str) -> bool:
        try:
            esquema, iteracoes, sal_hex, digest_hex = armazenado.split("$")
            if esquema != "pbkdf2":
                return False
            novo = hashlib.pbkdf2_hmac(
                "sha256",
                senha.encode("utf-8"),
                bytes.fromhex(sal_hex),
                int(iteracoes),
            )
        except (ValueError, TypeError):
            return False
        return secrets.compare_digest(novo.hex(), digest_hex)
