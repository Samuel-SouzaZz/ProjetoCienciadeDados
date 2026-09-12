"""
comum.py — funcoes compartilhadas pelas etapas do KDD.

Este modulo NAO executa nada por conta propria. Ele apenas reune:
  * a configuracao de leitura do CSV bruto da PRF (separador, encoding, decimal);
  * utilitarios de texto (remocao de espacos/caracteres invisiveis);
  * calculo de hash de arquivo (para o validador registrar QUAL arquivo auditou);
  * leitura do contrato de qualidade em JSON;
  * um registrador de auditoria (arquivo, linha/ID, regra, valor antes, valor depois).

Motivo de existir: as etapas diagnostico/limpeza/validacao/analise/treino precisam
concordar sobre como o arquivo bruto e lido. Se cada script decidisse por conta
propria, o resultado deixaria de ser reproduzivel.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Caminhos do projeto (todos derivados da pasta raiz, nada de caminho absoluto)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROC = RAIZ / "data" / "processed"
DIR_QUAR = RAIZ / "data" / "quarantine"
DIR_CONFIG = RAIZ / "config"
DIR_REPORTS = RAIZ / "reports"
DIR_DOCS = RAIZ / "docs"

ARQ_CONTRATO = DIR_CONFIG / "regras_qualidade.json"

# Nome do CSV bruto entregue pela atividade (ZIP do Google Drive).
NOME_CSV_BRUTO = "acidentes2025_todas_causas_tipos.csv"

# ---------------------------------------------------------------------------
# Configuracao de leitura do arquivo BRUTO da PRF.
# Confirmada por inspecao dos bytes do arquivo, nao por suposicao:
#   - separador ';'  (cabecalho: "id";"pesid";"data_inversa";...)
#   - encoding latin-1: o byte 0xE7 ("c" cedilha) quebra a decodificacao UTF-8
#   - decimal ','     (km = 89,5 ; latitude = -8,20760697)
#   - texto entre aspas duplas
#   - token de ausencia "NA" e "(null)"
# ---------------------------------------------------------------------------
LEITURA_BRUTO = {
    "sep": ";",
    "encoding": "latin-1",
    "decimal": ",",
    "quotechar": '"',
}

# Tokens que representam ausencia no arquivo bruto. Sao tratados como nulo na
# LEITURA, mas cada coluna decide depois se o nulo e aceitavel (ver contrato).
TOKENS_AUSENCIA = ["NA", "na", "N/A", "(null)", "NULL", "null", ""]

# ---------------------------------------------------------------------------
# Configuracao de escrita do CSV LIMPO (exigida pelo enunciado).
# utf-8-sig = UTF-8 com BOM, para o Excel do Windows abrir com acentos corretos.
# ---------------------------------------------------------------------------
ESCRITA_LIMPO = {
    "sep": ";",
    "encoding": "utf-8-sig",
    "decimal": ",",
    "index": False,
}

# Caracteres invisiveis que aparecem com frequencia em bases publicas.
INVISIVEIS = re.compile(r"[\u00a0\u200b\u200c\u200d\ufeff\t\r\n]+")
ESPACOS_MULTIPLOS = re.compile(r"\s{2,}")


def garantir_pastas() -> None:
    """Cria as pastas de saida se ainda nao existirem (nao apaga nada)."""
    for d in (DIR_RAW, DIR_PROC, DIR_QUAR, DIR_CONFIG, DIR_REPORTS, DIR_DOCS):
        d.mkdir(parents=True, exist_ok=True)


def limpar_texto(valor):
    """Remove caracteres invisiveis e espacos duplicados de UM valor textual.

    Nao muda maiusculas/minusculas nem acentos: os rotulos legiveis em portugues
    precisam ser preservados no CSV limpo.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return pd.NA
    texto = str(valor)
    texto = unicodedata.normalize("NFC", texto)
    texto = INVISIVEIS.sub(" ", texto)
    texto = ESPACOS_MULTIPLOS.sub(" ", texto).strip()
    return texto if texto else pd.NA


def chave_comparacao(valor) -> str:
    """Versao 'sem acento, minuscula, sem espaco extra' usada SOMENTE para comparar.

    Serve para reconhecer que "Ceu Claro", "CEU CLARO" e "C?u  Claro" sao a mesma
    categoria. O valor gravado no CSV continua sendo o rotulo legivel.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return ESPACOS_MULTIPLOS.sub(" ", texto)


def hash_arquivo(caminho: Path, algoritmo: str = "sha256") -> str:
    """SHA-256 do arquivo, lido em blocos para nao carregar 223 MB na memoria."""
    h = hashlib.new(algoritmo)
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def carregar_contrato(caminho: Path = ARQ_CONTRATO) -> dict:
    """Le config/regras_qualidade.json. Falha alto se o contrato nao existir."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Contrato de qualidade nao encontrado: {caminho}. "
            "Ele e obrigatorio: as regras nao podem ser inventadas em tempo de execucao."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def ambiente() -> dict:
    """Versoes usadas na execucao, para a ficha tecnica e reprodutibilidade."""
    import matplotlib
    import sklearn

    return {
        "executado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "sistema": f"{platform.system()} {platform.release()}",
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "matplotlib": matplotlib.__version__,
    }


def salvar_json(dados: dict, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def tabela_markdown(df: pd.DataFrame) -> str:
    """Converte um DataFrame em tabela markdown sem depender do pacote 'tabulate'."""
    if df.empty:
        return "_(sem linhas)_"
    cols = [str(c) for c in df.columns]
    linhas = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        celulas = ["" if pd.isna(v) else str(v).replace("|", "\\|") for v in r.tolist()]
        linhas.append("| " + " | ".join(celulas) + " |")
    return "\n".join(linhas)


class Auditoria:
    """Acumula 'o que foi mudado, onde e por qual regra'.

    Cada linha do registro guarda: arquivo de origem, id/linha de origem, coluna,
    regra aplicada, valor anterior e valor posterior. E isso que permite provar
    que a limpeza foi deterministica em vez de 'magica'.
    """

    def __init__(self, arquivo_origem: str):
        self.arquivo_origem = arquivo_origem
        self._itens: list[dict] = []

    def registrar(self, id_origem, coluna, regra, antes, depois, linha_origem=None):
        self._itens.append(
            {
                "arquivo_origem": self.arquivo_origem,
                "linha_origem": linha_origem,
                "id_origem": id_origem,
                "coluna": coluna,
                "regra": regra,
                "valor_anterior": antes,
                "valor_posterior": depois,
            }
        )

    def __len__(self) -> int:
        return len(self._itens)

    def para_dataframe(self) -> pd.DataFrame:
        colunas = [
            "arquivo_origem",
            "linha_origem",
            "id_origem",
            "coluna",
            "regra",
            "valor_anterior",
            "valor_posterior",
        ]
        if not self._itens:
            return pd.DataFrame(columns=colunas)
        return pd.DataFrame(self._itens, columns=colunas)

    def salvar(self, caminho: Path, limite_linhas: int | None = 200_000) -> dict:
        """Grava o registro de auditoria. Se for gigante, grava uma amostra e avisa."""
        df = self.para_dataframe()
        total = len(df)
        truncado = False
        if limite_linhas is not None and total > limite_linhas:
            df = df.head(limite_linhas)
            truncado = True
        caminho.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(caminho, sep=";", encoding="utf-8-sig", index=False)
        return {
            "arquivo": str(caminho),
            "registros_auditoria": int(total),
            "gravados": int(len(df)),
            "truncado": truncado,
        }
