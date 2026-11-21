"""Formata centavos como real brasileiro."""


class FormatadorMoeda:
    def formatar(self, centavos: int) -> str:
        texto = f"R$ {centavos / 100:,.2f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
