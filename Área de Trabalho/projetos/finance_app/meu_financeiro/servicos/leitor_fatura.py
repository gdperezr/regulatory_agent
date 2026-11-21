"""Lê o PDF da fatura e devolve as despesas, sem gravar nada."""

import re
from datetime import date
from io import BytesIO

import pdfplumber

from meu_financeiro.dominio.lancamento_fatura import LancamentoFatura
from meu_financeiro.dominio.leitura_fatura import LeituraFatura
from meu_financeiro.excecoes_financeiras import DadosInvalidos, FaturaNaoLida


class LeitorFatura:
    """Funciona com o PDF de texto baixado no banco. Foto e PDF escaneado ficam de fora."""

    _LIMITE_LINHAS = 500
    _MESES = {
        "JAN": 1,
        "FEV": 2,
        "MAR": 3,
        "ABR": 4,
        "MAI": 5,
        "JUN": 6,
        "JUL": 7,
        "AGO": 8,
        "SET": 9,
        "OUT": 10,
        "NOV": 11,
        "DEZ": 12,
    }
    _DATA_NO_INICIO = re.compile(
        r"^(?P<dia>\d{2})/(?P<mes>\d{2})(?:/(?P<ano>\d{2,4}))?\s+(?P<resto>.+)$"
    )
    _DATA_NOME_MES = re.compile(
        r"^(?P<dia>\d{2})\s+(?P<nome>JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)"
        r"(?:\s+(?P<ano>\d{4}))?\s+(?P<resto>.+)$",
        re.IGNORECASE,
    )
    _VALOR_FINAL = re.compile(
        r"(?P<valor>-?\d{1,3}(?:\.\d{3})*,\d{2})\s*(?P<sinal>[CD])?$",
        re.IGNORECASE,
    )
    _PARCELA = re.compile(
        r"(?:PARC(?:ELA)?\.?\s*)?(?P<atual>\d{1,2})\s*(?:/|DE)\s*(?P<total>\d{1,2})",
        re.IGNORECASE,
    )

    def ler(self, conteudo: bytes, mes_fatura: str) -> LeituraFatura:
        self._validar_mes(mes_fatura)
        texto_tabela, texto_pagina = self._extrair_partes(conteudo)
        opcoes = []
        for texto in (texto_tabela, texto_pagina):
            if not texto.strip():
                continue
            try:
                opcoes.append(self.ler_texto(texto, mes_fatura))
            except FaturaNaoLida:
                continue
        if not opcoes:
            raise FaturaNaoLida(
                "Não encontrei despesas nesse PDF. Use o arquivo baixado no aplicativo "
                "ou no site do banco. Foto da fatura não é lida."
            )
        melhor = max(opcoes, key=lambda item: len(item.lancamentos))
        return LeituraFatura(
            banco=self._detectar_banco(f"{texto_tabela}\n{texto_pagina}"),
            lancamentos=melhor.lancamentos,
            ignorados=melhor.ignorados,
            avisos=melhor.avisos,
        )

    def ler_texto(self, texto: str, mes_fatura: str) -> LeituraFatura:
        self._validar_mes(mes_fatura)
        lancamentos: list[LancamentoFatura] = []
        ignorados: list[str] = []
        avisos: list[str] = []
        vistos: set[tuple] = set()
        for bruta in self._quebrar_linhas(texto):
            if len(lancamentos) >= self._LIMITE_LINHAS:
                avisos.append("A leitura parou em 500 lançamentos.")
                break
            resultado = self._interpretar(bruta, mes_fatura)
            if resultado is None:
                continue
            if isinstance(resultado, str):
                ignorados.append(resultado)
                continue
            chave = (
                resultado.data.isoformat(),
                resultado.descricao.upper(),
                resultado.valor_centavos,
                resultado.numero_parcela,
                resultado.total_parcelas,
            )
            if chave in vistos:
                continue
            vistos.add(chave)
            lancamentos.append(resultado)
        if not lancamentos and not ignorados:
            raise FaturaNaoLida(
                "Não encontrei despesas nesse PDF. Use o arquivo baixado no aplicativo "
                "ou no site do banco. Foto da fatura não é lida."
            )
        return LeituraFatura(
            banco=self._detectar_banco(texto),
            lancamentos=lancamentos,
            ignorados=ignorados,
            avisos=avisos,
        )

    def _extrair_partes(self, conteudo: bytes) -> tuple[str, str]:
        if not conteudo:
            raise FaturaNaoLida("O arquivo da fatura está vazio.")
        tabelas: list[str] = []
        paginas: list[str] = []
        try:
            with pdfplumber.open(BytesIO(conteudo)) as pdf:
                if not pdf.pages:
                    raise FaturaNaoLida("O PDF não tem páginas.")
                for pagina in pdf.pages:
                    for tabela in pagina.extract_tables() or []:
                        for linha in tabela:
                            if not linha:
                                continue
                            texto = " ".join(celula.strip() for celula in linha if celula and celula.strip())
                            if texto:
                                tabelas.append(texto)
                    texto_pagina = pagina.extract_text() or ""
                    if texto_pagina.strip():
                        paginas.append(texto_pagina)
        except FaturaNaoLida:
            raise
        except Exception as erro:
            mensagem = str(erro).lower()
            if "password" in mensagem or "encrypt" in mensagem:
                raise FaturaNaoLida("Esse PDF tem senha. Baixe a fatura de novo, sem senha.") from erro
            raise FaturaNaoLida("Não consegui abrir esse PDF. Use o arquivo baixado no banco.") from erro
        if not tabelas and not paginas:
            raise FaturaNaoLida(
                "Esse PDF não tem texto para ler. Baixe a fatura no aplicativo do banco, em vez de fotografar."
            )
        return "\n".join(tabelas), "\n".join(paginas)

    def _quebrar_linhas(self, texto: str) -> list[str]:
        linhas = []
        for bruta in texto.splitlines():
            linha = re.sub(r"\s+", " ", bruta.replace("|", " ").replace("R$", " ")).strip()
            if not linha:
                continue
            partes = re.split(r"(?<=,\d{2})\s+(?=\d{2}/\d{2}\b)", linha)
            linhas.extend(parte.strip() for parte in partes if parte.strip())
        return linhas

    def _interpretar(self, linha: str, mes_fatura: str) -> LancamentoFatura | str | None:
        data_texto, resto = self._separar_data(linha)
        if data_texto is None or not resto:
            return None
        valor = self._VALOR_FINAL.search(resto)
        if valor is None:
            return None
        descricao = resto[: valor.start()].strip(" -")
        descricao = re.sub(r"\s+", " ", descricao)
        if len(descricao) < 2:
            return None
        if self._parece_credito(valor.group("valor"), valor.group("sinal")):
            return f"{descricao} (crédito, não entra como despesa)"
        if self._ignorar(descricao):
            return f"{descricao} (pagamento ou total, não entra como despesa)"
        try:
            data_compra = self._montar_data(data_texto, mes_fatura)
            centavos = self._centavos(valor.group("valor"))
        except (DadosInvalidos, ValueError):
            return None
        if centavos <= 0:
            return None
        numero, total = self._parcela(descricao)
        return LancamentoFatura(
            data=data_compra,
            descricao=descricao[:120],
            valor_centavos=centavos,
            numero_parcela=numero,
            total_parcelas=total,
        )

    def _separar_data(self, linha: str) -> tuple[str | None, str]:
        numerica = self._DATA_NO_INICIO.match(linha)
        if numerica:
            ano = numerica.group("ano")
            data = f"{numerica.group('dia')}/{numerica.group('mes')}"
            if ano:
                data = f"{data}/{ano}"
            return data, numerica.group("resto")
        por_nome = self._DATA_NOME_MES.match(linha)
        if por_nome:
            mes = self._MESES[por_nome.group("nome").upper()]
            data = f"{por_nome.group('dia')}/{mes:02d}"
            if por_nome.group("ano"):
                data = f"{data}/{por_nome.group('ano')}"
            return data, por_nome.group("resto")
        return None, ""

    def _montar_data(self, texto: str, mes_fatura: str) -> date:
        ano_fatura, mes_da_fatura = (int(parte) for parte in mes_fatura.split("-"))
        pedacos = texto.split("/")
        dia = int(pedacos[0])
        mes = int(pedacos[1])
        if len(pedacos) == 3:
            ano = int(pedacos[2])
            if ano < 100:
                ano += 2000
        else:
            ano = ano_fatura - 1 if mes > mes_da_fatura else ano_fatura
        if not 1 <= mes <= 12:
            raise DadosInvalidos("Data inválida na fatura.")
        return date(ano, mes, dia)

    def _centavos(self, texto: str) -> int:
        inteiro, decimal = texto.replace("-", "").split(",")
        return int(inteiro.replace(".", "")) * 100 + int(decimal)

    def _parcela(self, descricao: str) -> tuple[int, int]:
        for encontrado in self._PARCELA.finditer(descricao):
            atual = int(encontrado.group("atual"))
            total = int(encontrado.group("total"))
            if 1 <= atual <= total <= 48:
                return atual, total
        return 1, 1

    def _parece_credito(self, valor: str, sinal: str | None) -> bool:
        if valor.startswith("-"):
            return True
        return bool(sinal and sinal.upper() == "C")

    def _ignorar(self, descricao: str) -> bool:
        texto = descricao.upper()
        if texto.startswith(("TOTAL", "SUBTOTAL", "SALDO", "LIMITE", "VENCIMENTO", "PAGAMENTO", "PAGTO")):
            return True
        return "PAGAMENTO" in texto and "FATURA" in texto

    def _detectar_banco(self, texto: str) -> str:
        comparacao = texto.lower()
        if "banco do brasil" in comparacao or "bb.com.br" in comparacao:
            return "Banco do Brasil"
        if "itaú" in comparacao or "itau" in comparacao:
            return "Itaú"
        if "banco inter" in comparacao or "inter.co" in comparacao:
            return "Inter"
        if "santander" in comparacao:
            return "Santander"
        return "Banco não identificado"

    def _validar_mes(self, mes_fatura: str) -> None:
        if not re.fullmatch(r"\d{4}-\d{2}", mes_fatura):
            raise DadosInvalidos("Informe o mês da fatura.")
        mes = int(mes_fatura[5:7])
        if not 1 <= mes <= 12:
            raise DadosInvalidos("Informe o mês da fatura.")
