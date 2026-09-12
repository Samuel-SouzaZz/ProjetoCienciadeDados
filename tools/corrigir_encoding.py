r"""
corrigir_encoding.py - utilitario de manutencao do projeto (nao faz parte do KDD).

O editor usado para criar os arquivos grava em cp1252 (padrao do Windows PT-BR).
Python 3 exige UTF-8 no codigo-fonte. Este script percorre os arquivos de texto do
projeto e converte para UTF-8 (sem BOM) quando eles ainda nao estao em UTF-8.

Uso:
  python tools\corrigir_encoding.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PADROES = ("src/*.py", "tests/*.py", "tools/*.py", "docs/*.md", "*.md", "config/*.json")


def converter(caminho: Path) -> str:
    bruto = caminho.read_bytes()
    try:
        texto = bruto.decode("utf-8")
        status = "utf-8"
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252")
        status = "convertido de cp1252"
    normalizado = texto.replace("\r\n", "\n")
    novo = normalizado.encode("utf-8")
    if novo != bruto:
        caminho.write_bytes(novo)
        if status == "utf-8":
            status = "normalizado (fim de linha)"
    return status


def main() -> int:
    for padrao in PADROES:
        for caminho in sorted(RAIZ.glob(padrao)):
            print(f"{caminho.relative_to(RAIZ)}: {converter(caminho)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
