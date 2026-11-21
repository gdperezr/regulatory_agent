"""Pessoa que entra no Meu Financeiro."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Usuario:
    id: int | None
    nome: str
    login: str

    @classmethod
    def da_linha(cls, linha) -> "Usuario":
        return cls(id=linha["id"], nome=linha["name"], login=linha["login"])
