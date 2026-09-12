r"""
validar_dados.py - ETAPA 4: auditoria INDEPENDENTE da base exportada.

Este script NAO limpa, NAO preenche e NAO corrige nada. Ele reabre o CSV que a
limpeza gravou e pergunta: "este arquivo cumpre o contrato de qualidade?".

Por que isso importa: se a mesma funcao que limpa fosse usada para validar, ela
"consertaria" o problema durante a conferencia e sempre aprovaria. O validador
precisa ser um leitor desconfiado, nao um faxineiro.

Como a leitura e feita:
    pd.read_csv(..., dtype=str, keep_default_na=False, na_filter=False)
  Ou seja, TUDO entra como texto literal, inclusive celulas vazias, que ficam
  como "" em vez de NaN. Assim conseguimos ver o formato exatamente como esta
  gravado. Conversoes numericas/temporais aparecem so dentro das regras, como
  ferramenta temporaria de conferencia de tipo, sem alterar o DataFrame lido.

O que e verificado (cada regra com identificador, severidade e evidencia):
  E0xx  estrutura do arquivo (legivel, colunas, indice, chave, duplicatas)
  C1xx  por coluna: ausencia permitida, formato, tipo, dominio, intervalo
  T2xx  temporais: data e hora possiveis e no formato canonico
  X3xx  consistencia entre campos e atributos derivados (R01..R15 do contrato)
  M4xx  reconciliacao das linhas e elegibilidade para o modelo

Status global:
  APROVADA                 - nenhuma regra critica falhou nem ficou nao verificada
  APROVADA_COM_RESSALVAS   - so avisos falharam
  REPROVADA                - alguma regra critica falhou ou nao pode ser verificada

Codigos de saida: 0 aprovada (com ou sem ressalvas), 1 falha de qualidade,
                  2 erro operacional.

Uso:
  python src\validar_dados.py
  python src\validar_dados.py --arquivo data\processed\prf_limpo.csv
  python src\validar_dados.py --arquivo tests\tmp\caso.csv --sem-reconciliacao
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

try:
    from comum import (
        ARQ_CONTRATO,
        DIR_PROC,
        DIR_REPORTS,
        ambiente,
        carregar_contrato,
        garantir_pastas,
        hash_arquivo,
        salvar_json,
        tabela_markdown,
    )
except ModuleNotFoundError:  # permite chamar de fora da pasta src
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from comum import (  # noqa: F401
        ARQ_CONTRATO,
        DIR_PROC,
        DIR_REPORTS,
        ambiente,
        carregar_contrato,
        garantir_pastas,
        hash_arquivo,
        salvar_json,
        tabela_markdown,
    )

PASSOU = "PASSOU"
FALHOU = "FALHOU"
NAO_APLICAVEL = "NAO_APLICAVEL"
NAO_VERIFICADA = "NAO_VERIFICADA"

RE_INTEIRO = re.compile(r"^-?\d+$")
RE_DECIMAL = re.compile(r"^-?\d+(,\d+)?$")
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$")


class Relatorio:
    """Acumula o resultado de cada regra, com evidencia rastreavel."""

    def __init__(self, total_linhas: int, coluna_chave: str = "id"):
        self.regras: list[dict] = []
        self.total_linhas = total_linhas
        self.coluna_chave = coluna_chave

    def add(
        self,
        identificador: str,
        descricao: str,
        severidade: str,
        status: str,
        linhas_avaliadas: int = 0,
        violacoes: int = 0,
        exemplos: list | None = None,
        detalhe: str = "",
    ) -> None:
        pct = round(100 * violacoes / linhas_avaliadas, 6) if linhas_avaliadas else 0.0
        self.regras.append(
            {
                "id": identificador,
                "descricao": descricao,
                "severidade": severidade,
                "status": status,
                "linhas_avaliadas": int(linhas_avaliadas),
                "violacoes": int(violacoes),
                "pct_violacoes": pct,
                "exemplos": (exemplos or [])[:5],
                "detalhe": detalhe,
            }
        )

    def checar(
        self,
        identificador: str,
        descricao: str,
        severidade: str,
        mascara_violacao: pd.Series,
        df: pd.DataFrame,
        colunas_exemplo: list[str],
        detalhe: str = "",
    ) -> None:
        """Registra uma regra a partir de uma mascara booleana de violacoes.

        Os exemplos guardam a chave (id) e as colunas relevantes, para que quem
        le o relatorio possa achar o registro no CSV.
        """
        n = int(mascara_violacao.sum())
        exemplos = []
        if n:
            cols: list[str] = []
            for c in [self.coluna_chave] + colunas_exemplo:
                if c in df.columns and c not in cols:
                    cols.append(c)
            exemplos = df.loc[mascara_violacao, cols].head(5).to_dict(orient="records")
        self.add(
            identificador, descricao, severidade,
            FALHOU if n else PASSOU,
            linhas_avaliadas=len(df), violacoes=n, exemplos=exemplos, detalhe=detalhe,
        )

    # ---- consolidacao ----
    def status_global(self) -> str:
        criticas_ruins = [
            r for r in self.regras
            if r["severidade"] == "critico" and r["status"] in (FALHOU, NAO_VERIFICADA)
        ]
        if criticas_ruins:
            return "REPROVADA"
        avisos_ruins = [
            r for r in self.regras
            if r["severidade"] == "aviso" and r["status"] in (FALHOU, NAO_VERIFICADA)
        ]
        return "APROVADA_COM_RESSALVAS" if avisos_ruins else "APROVADA"

    def ressalvas(self) -> list[str]:
        return [
            f"[{r['id']}] {r['descricao']} - {r['violacoes']} violacao(oes) "
            f"({r['pct_violacoes']}%)"
            for r in self.regras
            if r["severidade"] in ("aviso", "informativo") and r["status"] in (FALHOU, NAO_VERIFICADA)
        ]

    def contagem_por_status(self) -> dict:
        return pd.Series([r["status"] for r in self.regras]).value_counts().to_dict()

    def dataframe(self) -> pd.DataFrame:
        d = pd.DataFrame(self.regras)
        d["exemplos"] = d["exemplos"].map(lambda e: " | ".join(str(x) for x in e))
        return d


# ---------------------------------------------------------------------------
# Auxiliares. Sao conversoes TEMPORARIAS: nao substituem valores no DataFrame.
# ---------------------------------------------------------------------------
def como_inteiro(serie_texto: pd.Series) -> pd.Series:
    return pd.to_numeric(serie_texto.where(serie_texto != ""), errors="coerce")


def como_decimal(serie_texto: pd.Series) -> pd.Series:
    return pd.to_numeric(
        serie_texto.where(serie_texto != "").str.replace(",", ".", regex=False),
        errors="coerce",
    )


def data_valida(texto: str) -> bool:
    """True quando o texto e uma data real no formato canonico aaaa-mm-dd.

    31/02 nao existe: strptime rejeita, e por isso 'data impossivel' e detectada.
    """
    if not RE_DATA.match(texto):
        return False
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def dominio_da_coluna(regra_coluna: dict) -> list[str] | None:
    return regra_coluna.get("dominio_acentuado") or regra_coluna.get("dominio")


def componentes_permitidos(regra_coluna: dict) -> list[str] | None:
    return (
        regra_coluna.get("componentes_permitidos_acentuado")
        or regra_coluna.get("componentes_permitidos")
    )


# ---------------------------------------------------------------------------
# Blocos de verificacao
# ---------------------------------------------------------------------------
def validar_estrutura(df: pd.DataFrame, contrato: dict, rel: Relatorio) -> None:
    colunas = list(df.columns)
    obrigatorias = list(contrato["colunas"].keys())

    faltando = [c for c in obrigatorias if c not in colunas]
    rel.add("E001", "Todas as colunas declaradas no contrato estao presentes.", "critico",
            FALHOU if faltando else PASSOU, len(colunas), len(faltando),
            exemplos=faltando, detalhe=f"ausentes: {faltando}" if faltando else "")

    duplicados = [c for c in set(colunas) if colunas.count(c) > 1]
    rel.add("E002", "Nomes de coluna sao unicos.", "critico",
            FALHOU if duplicados else PASSOU, len(colunas), len(duplicados),
            exemplos=duplicados)

    suspeitas_indice = [
        c for c in colunas
        if c.startswith("Unnamed") or c.strip() == "" or c.lower() in ("index", "level_0")
    ]
    rel.add("E003", "Nenhuma coluna de indice foi exportada por acidente.", "critico",
            FALHOU if suspeitas_indice else PASSOU, len(colunas), len(suspeitas_indice),
            exemplos=suspeitas_indice)

    inesperadas = [c for c in colunas if c not in obrigatorias]
    rel.add("E004", "Nenhuma coluna fora do contrato.", "aviso",
            FALHOU if inesperadas else PASSOU, len(colunas), len(inesperadas),
            exemplos=inesperadas)

    rel.add("E005", "O arquivo tem ao menos uma linha de dados.", "critico",
            PASSOU if len(df) > 0 else FALHOU, len(df), 0 if len(df) else 1)

    chave = contrato["chave_primaria"]
    if all(c in df.columns for c in chave):
        vazia = (df[chave[0]].astype(str).str.strip() == "").sum()
        rel.add("E006", f"Chave primaria {chave} preenchida em todas as linhas.", "critico",
                FALHOU if vazia else PASSOU, len(df), int(vazia))
        dup = df.duplicated(subset=chave, keep=False)
        rel.checar("E007", f"Chave primaria {chave} e unica.", "critico", dup, df, chave)
    else:
        rel.add("E006", f"Chave primaria {chave} preenchida.", "critico", NAO_VERIFICADA,
                detalhe="coluna de chave ausente no arquivo")
        rel.add("E007", f"Chave primaria {chave} e unica.", "critico", NAO_VERIFICADA,
                detalhe="coluna de chave ausente no arquivo")

    dup_total = df.duplicated(keep=False)
    rel.checar("E008", "Nenhuma linha e integralmente duplicada.", "critico",
               dup_total, df, [])


def validar_colunas(df: pd.DataFrame, contrato: dict, rel: Relatorio) -> None:
    for coluna, regra in contrato["colunas"].items():
        if coluna not in df.columns:
            rel.add(f"C1-{coluna}", f"Regras da coluna '{coluna}'.",
                    regra.get("severidade", "aviso"), NAO_VERIFICADA,
                    detalhe="coluna ausente no arquivo")
            continue

        serie = df[coluna].astype(str)
        vazio = serie == ""
        preenchido = ~vazio
        sev = regra.get("severidade", "aviso")

        # ---- ausencia permitida ou nao ----
        if regra.get("nulo_permitido", True):
            rel.add(f"C10-{coluna}", f"'{coluna}' aceita ausencia (politica do contrato).",
                    "informativo", PASSOU, len(df), int(vazio.sum()),
                    detalhe=f"{int(vazio.sum())} celulas vazias, permitidas")
        else:
            rel.checar(f"C10-{coluna}", f"'{coluna}' nao pode ficar vazia.", sev,
                       vazio, df, [coluna])

        # ---- espacos nas bordas ----
        rel.checar(f"C11-{coluna}", f"'{coluna}' sem espaco no inicio ou no fim.", "aviso",
                   preenchido & (serie != serie.str.strip()), df, [coluna])

        # ---- formato por regex declarado ----
        if regra.get("regex"):
            padrao = re.compile(regra["regex"])
            ruim = preenchido & ~serie.str.match(padrao)
            rel.checar(f"C20-{coluna}", f"'{coluna}' respeita o padrao {regra['regex']}.",
                       sev, ruim, df, [coluna])

        # ---- tipo ----
        tipo = regra.get("tipo")
        if tipo == "inteiro":
            ruim = preenchido & ~serie.str.match(RE_INTEIRO)
            rel.checar(f"C30-{coluna}", f"'{coluna}' e inteiro, sem parte fracionaria.",
                       sev, ruim, df, [coluna],
                       detalhe="valores como '3,0' ou '3.0' sao violacao")
        elif tipo == "decimal":
            ruim = preenchido & ~serie.str.match(RE_DECIMAL)
            rel.checar(f"C30-{coluna}",
                       f"'{coluna}' e decimal com virgula como separador.", sev, ruim,
                       df, [coluna])

        # ---- intervalo numerico ----
        if tipo in ("inteiro", "decimal") and (
            "minimo" in regra or "maximo" in regra
        ):
            num = como_decimal(serie) if tipo == "decimal" else como_inteiro(serie)
            fora = pd.Series(False, index=df.index)
            if "minimo" in regra:
                fora |= num.notna() & (num < regra["minimo"])
            if "maximo" in regra:
                fora |= num.notna() & (num > regra["maximo"])
            rel.checar(f"C40-{coluna}",
                       f"'{coluna}' dentro de [{regra.get('minimo')}, {regra.get('maximo')}].",
                       sev, fora, df, [coluna])

        # ---- dominio de categoria ----
        dom = dominio_da_coluna(regra)
        if tipo == "categoria" and dom:
            fora = preenchido & ~serie.isin(dom)
            rel.checar(f"C50-{coluna}", f"'{coluna}' usa apenas as categorias do contrato.",
                       sev, fora, df, [coluna],
                       detalhe=f"origem da regra: {regra.get('origem_regra')}; dominio: {dom}")

        # ---- categoria multivalorada (tracado_via) ----
        comps = componentes_permitidos(regra)
        if tipo == "categoria_multivalorada" and comps:
            sep = regra.get("separador_interno", ";")
            permitidos = set(comps)

            def componentes_invalidos(v: str) -> bool:
                return bool({p.strip() for p in v.split(sep) if p.strip()} - permitidos)

            def fora_de_ordem(v: str) -> bool:
                partes = [p.strip() for p in v.split(sep) if p.strip()]
                return partes != sorted(set(partes))

            rel.checar(f"C51-{coluna}", f"'{coluna}' usa apenas componentes permitidos.",
                       sev, preenchido & serie.map(componentes_invalidos), df, [coluna],
                       detalhe=f"componentes: {sorted(permitidos)}")
            rel.checar(f"C52-{coluna}",
                       f"'{coluna}' tem componentes em ordem alfabetica e sem repeticao.",
                       sev, preenchido & serie.map(fora_de_ordem), df, [coluna],
                       detalhe="e o que garante que 'Reta;Declive' e 'Declive;Reta' virem o mesmo rotulo")


def validar_temporais(df: pd.DataFrame, contrato: dict, rel: Relatorio) -> None:
    col_data, col_hora = "data_inversa", "horario"

    if col_data in df.columns:
        serie = df[col_data].astype(str)
        preenchido = serie != ""
        rel.checar("T201", "data_inversa e uma data real no formato canonico aaaa-mm-dd.",
                   "critico", preenchido & ~serie.map(data_valida), df, [col_data],
                   detalhe="detecta formato errado E datas impossiveis como 2025-02-30")
        validas = serie[preenchido & serie.map(data_valida)]
        if len(validas):
            conv = pd.to_datetime(validas, format="%Y-%m-%d")
            faixa = contrato["colunas"][col_data].get("intervalo_data")
            if faixa:
                ini, fim = pd.Timestamp(faixa[0]), pd.Timestamp(faixa[1])
                fora = pd.Series(False, index=df.index)
                fora.loc[conv.index] = (conv < ini) | (conv > fim)
                rel.checar("T202", f"data_inversa dentro do periodo declarado {faixa}.",
                           "critico", fora, df, [col_data])
            futuro = pd.Series(False, index=df.index)
            futuro.loc[conv.index] = conv.dt.date > date.today()
            rel.checar("T203", "data_inversa nao esta no futuro.", "aviso", futuro, df, [col_data])
        else:
            rel.add("T202", "data_inversa dentro do periodo declarado.", "critico",
                    NAO_VERIFICADA, detalhe="nenhuma data valida para avaliar")
    else:
        for rid in ("T201", "T202", "T203"):
            rel.add(rid, "Regras de data_inversa.", "critico", NAO_VERIFICADA,
                    detalhe="coluna ausente")

    if col_hora in df.columns:
        serie = df[col_hora].astype(str)
        preenchido = serie != ""
        rel.checar("T204", "horario e hora possivel no formato canonico HH:MM:SS.",
                   "critico", preenchido & ~serie.str.match(RE_HORA), df, [col_hora])
    else:
        rel.add("T204", "Regras de horario.", "critico", NAO_VERIFICADA,
                detalhe="coluna ausente")


def validar_consistencia(df: pd.DataFrame, contrato: dict, rel: Relatorio) -> None:
    """Regras R01..R15 do contrato, entre campos e atributos derivados."""
    regras = {r["id"]: r for r in contrato["regras_entre_campos"]}

    def sev(rid: str) -> str:
        return regras.get(rid, {}).get("severidade", "aviso")

    def desc(rid: str) -> str:
        return regras.get(rid, {}).get("descricao", rid)

    def precisa(cols: list[str]) -> bool:
        faltam = [c for c in cols if c not in df.columns]
        return not faltam

    txt = {c: df[c].astype(str) for c in df.columns}
    inteiro = {}
    for c in ("qtd_pessoas", "qtd_ilesos", "qtd_feridos_leves", "qtd_feridos_graves",
              "qtd_feridos", "qtd_mortos", "qtd_estado_fisico_nao_informado",
              "qtd_veiculos", "ano", "mes", "hora"):
        if c in df.columns:
            inteiro[c] = como_inteiro(txt[c])

    # R01
    cols = ["qtd_pessoas", "qtd_ilesos", "qtd_feridos_leves", "qtd_feridos_graves",
            "qtd_mortos", "qtd_estado_fisico_nao_informado"]
    if precisa(cols):
        soma = (inteiro["qtd_ilesos"] + inteiro["qtd_feridos_leves"]
                + inteiro["qtd_feridos_graves"] + inteiro["qtd_mortos"]
                + inteiro["qtd_estado_fisico_nao_informado"])
        rel.checar("X301", desc("R01"), sev("R01"),
                   inteiro["qtd_pessoas"].notna() & (inteiro["qtd_pessoas"] != soma),
                   df, cols)
    else:
        rel.add("X301", desc("R01"), sev("R01"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R02
    if precisa(["qtd_feridos", "qtd_feridos_leves", "qtd_feridos_graves"]):
        rel.checar("X302", desc("R02"), sev("R02"),
                   inteiro["qtd_feridos"] != inteiro["qtd_feridos_leves"] + inteiro["qtd_feridos_graves"],
                   df, ["qtd_feridos", "qtd_feridos_leves", "qtd_feridos_graves"])
    else:
        rel.add("X302", desc("R02"), sev("R02"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R03, R04, R05 - relacao entre gravidade e contagens
    if precisa(["classificacao_acidente", "qtd_feridos", "qtd_mortos"]):
        g = txt["classificacao_acidente"]
        rel.checar("X303", desc("R03"), sev("R03"),
                   (g == "Sem Vítimas") & ((inteiro["qtd_feridos"] > 0) | (inteiro["qtd_mortos"] > 0)),
                   df, ["classificacao_acidente", "qtd_feridos", "qtd_mortos"])
        rel.checar("X304", desc("R04"), sev("R04"),
                   (g == "Com Vítimas Fatais") & (inteiro["qtd_mortos"] < 1),
                   df, ["classificacao_acidente", "qtd_mortos"])
        rel.checar("X305", desc("R05"), sev("R05"),
                   (g == "Com Vítimas Feridas")
                   & ((inteiro["qtd_feridos"] < 1) | (inteiro["qtd_mortos"] > 0)),
                   df, ["classificacao_acidente", "qtd_feridos", "qtd_mortos"])
    else:
        for rid, r in (("X303", "R03"), ("X304", "R04"), ("X305", "R05")):
            rel.add(rid, desc(r), sev(r), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R06 - fim de semana
    if precisa(["fim_de_semana", "dia_semana_calculado"]):
        esperado = txt["dia_semana_calculado"].isin(["Sábado", "Domingo"]).map(
            {True: "Sim", False: "Não"}
        )
        rel.checar("X306", desc("R06"), sev("R06"), txt["fim_de_semana"] != esperado,
                   df, ["fim_de_semana", "dia_semana_calculado"])
    else:
        rel.add("X306", desc("R06"), sev("R06"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R07 e R09 - derivados da data
    if precisa(["data_inversa", "ano", "mes", "dia_semana_calculado"]):
        d = pd.to_datetime(txt["data_inversa"].where(txt["data_inversa"] != ""),
                           format="%Y-%m-%d", errors="coerce")
        rel.checar("X307", desc("R07"), sev("R07"),
                   d.notna() & ((inteiro["ano"] != d.dt.year) | (inteiro["mes"] != d.dt.month)),
                   df, ["data_inversa", "ano", "mes"])
        nomes = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
                 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
        rel.checar("X309", desc("R09"), sev("R09"),
                   d.notna() & (txt["dia_semana_calculado"] != d.dt.dayofweek.map(nomes)),
                   df, ["data_inversa", "dia_semana_calculado"])
    else:
        for rid, r in (("X307", "R07"), ("X309", "R09")):
            rel.add(rid, desc(r), sev(r), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R08 - hora e faixa horaria
    if precisa(["horario", "hora", "faixa_horaria"]):
        hora_do_texto = pd.to_numeric(
            txt["horario"].where(txt["horario"].str.match(RE_HORA)).str.slice(0, 2),
            errors="coerce",
        )
        rel.checar("X308a", "hora corresponde a hora cheia de horario.", sev("R08"),
                   hora_do_texto.notna() & (inteiro["hora"] != hora_do_texto),
                   df, ["horario", "hora"])
        limites = contrato["colunas"]["faixa_horaria"]["limites"]
        rotulos = {"Madrugada": range(0, 6), "Manhã": range(6, 12),
                   "Tarde": range(12, 18), "Noite": range(18, 24)}

        def faixa_esperada(h):
            if pd.isna(h):
                return ""
            for rotulo, faixa in rotulos.items():
                if int(h) in faixa:
                    return rotulo
            return ""

        esperada = hora_do_texto.map(faixa_esperada)
        rel.checar("X308b",
                   f"faixa_horaria respeita os limites do contrato ({limites}).",
                   sev("R08"), (esperada != "") & (txt["faixa_horaria"] != esperada),
                   df, ["horario", "faixa_horaria"])
    else:
        rel.add("X308a", desc("R08"), sev("R08"), NAO_VERIFICADA, detalhe="colunas ausentes")
        rel.add("X308b", desc("R08"), sev("R08"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R10 e R11 - sinalizadores do alvo
    if precisa(["classificacao_acidente", "alvo_ausente"]):
        esperado = (txt["classificacao_acidente"] == "").map({True: "Sim", False: "Não"})
        rel.checar("X310", desc("R10"), sev("R10"), txt["alvo_ausente"] != esperado,
                   df, ["classificacao_acidente", "alvo_ausente"])
    else:
        rel.add("X310", desc("R10"), sev("R10"), NAO_VERIFICADA, detalhe="colunas ausentes")

    if precisa(["alvo_ausente", "elegivel_modelo"]):
        rel.checar("X311", desc("R11"), sev("R11"),
                   (txt["alvo_ausente"] == "Sim") & (txt["elegivel_modelo"] != "Não"),
                   df, ["alvo_ausente", "elegivel_modelo"])
    else:
        rel.add("X311", desc("R11"), sev("R11"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R12 - km minimo do dicionario
    if "km" in df.columns:
        km = como_decimal(txt["km"])
        minimo = contrato["colunas"]["km"].get("minimo_dicionario", 0.1)
        rel.checar("X312", desc("R12"), sev("R12"), km.notna() & (km < minimo), df, ["km"],
                   detalhe="valores preservados de proposito: o dicionario nao da regra de correcao")
    else:
        rel.add("X312", desc("R12"), sev("R12"), NAO_VERIFICADA, detalhe="coluna ausente")

    # R13 - veiculos
    if "qtd_veiculos" in df.columns:
        rel.checar("X313", desc("R13"), sev("R13"),
                   inteiro["qtd_veiculos"].notna() & (inteiro["qtd_veiculos"] < 1),
                   df, ["qtd_veiculos"])
    else:
        rel.add("X313", desc("R13"), sev("R13"), NAO_VERIFICADA, detalhe="coluna ausente")

    # R14 - coordenadas
    if precisa(["latitude", "longitude"]):
        lat, lon = como_decimal(txt["latitude"]), como_decimal(txt["longitude"])
        c_lat = contrato["colunas"]["latitude"]
        c_lon = contrato["colunas"]["longitude"]
        fora = (
            (lat.notna() & ((lat < c_lat["minimo"]) | (lat > c_lat["maximo"])))
            | (lon.notna() & ((lon < c_lon["minimo"]) | (lon > c_lon["maximo"])))
        )
        rel.checar("X314", desc("R14"), sev("R14"), fora, df, ["latitude", "longitude"])
    else:
        rel.add("X314", desc("R14"), sev("R14"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R16 - a coluna de motivo so pode estar preenchida em linha inelegivel
    if precisa(["motivo_inelegibilidade", "elegivel_modelo"]):
        inelegivel = txt["elegivel_modelo"] == "Não"
        tem_motivo = txt["motivo_inelegibilidade"] != ""
        rel.checar("X316", desc("R16"), sev("R16"), inelegivel != tem_motivo, df,
                   ["elegivel_modelo", "motivo_inelegibilidade"],
                   detalhe="observacoes sobre entradas ausentes vao em 'entradas_ausentes'")
    else:
        rel.add("X316", desc("R16"), sev("R16"), NAO_VERIFICADA, detalhe="colunas ausentes")

    # R15 - espacos nas bordas em qualquer coluna textual
    total_espacos = 0
    for c in df.columns:
        s = txt[c]
        total_espacos += int(((s != "") & (s != s.str.strip())).sum())
    rel.add("X315", desc("R15"), sev("R15"), FALHOU if total_espacos else PASSOU,
            len(df) * len(df.columns), total_espacos)


def validar_reconciliacao_e_elegibilidade(
    df: pd.DataFrame, contrato: dict, rel: Relatorio, checar_reconciliacao: bool
) -> None:
    if not checar_reconciliacao:
        rel.add("M401", "Reconciliacao das linhas de entrada com os destinos.", "critico",
                NAO_APLICAVEL,
                detalhe="verificacao desligada por --sem-reconciliacao (caso de teste isolado)")
    else:
        caminho = DIR_REPORTS / "limpeza.json"
        if not caminho.exists():
            rel.add("M401", "Reconciliacao das linhas de entrada com os destinos.", "critico",
                    NAO_VERIFICADA,
                    detalhe=f"{caminho.name} nao encontrado; rode a limpeza antes de validar")
        else:
            import json

            limp = json.loads(caminho.read_text(encoding="utf-8"))
            r = limp["reconciliacao"]
            soma = (r["duplicatas_exatas_removidas"] + r["linhas_quarentena"]
                    + r["linhas_mantidas_agregadas"])
            ok_soma = soma == r["linhas_entrada"]
            ok_linhas = r["ocorrencias_resultantes"] == len(df)
            problemas = []
            if not ok_soma:
                problemas.append(
                    f"soma dos destinos {soma} != entrada {r['linhas_entrada']}")
            if not ok_linhas:
                problemas.append(
                    f"ocorrencias declaradas {r['ocorrencias_resultantes']} != linhas do CSV {len(df)}")
            rel.add("M401",
                    "Reconciliacao: entrada = duplicatas + quarentena + mantidas, e o "
                    "numero de ocorrencias declarado corresponde as linhas do CSV.",
                    "critico", FALHOU if problemas else PASSOU,
                    linhas_avaliadas=r["linhas_entrada"], violacoes=len(problemas),
                    exemplos=problemas, detalhe=f"origem: {caminho.name}")

    # elegibilidade linha a linha
    if "elegivel_modelo" in df.columns and "classificacao_acidente" in df.columns:
        txt = df["elegivel_modelo"].astype(str)
        fora = ~txt.isin(["Sim", "Não"])
        rel.checar("M402", "elegivel_modelo usa apenas Sim/Nao.", "critico", fora, df,
                   ["elegivel_modelo"])
        elegiveis = int((txt == "Sim").sum())
        rel.add("M403", "Ha registros elegiveis para o treino supervisionado.", "critico",
                PASSOU if elegiveis else FALHOU, len(df), 0 if elegiveis else len(df),
                detalhe=f"{elegiveis} de {len(df)} registros elegiveis")

        alvo = df.loc[txt == "Sim", "classificacao_acidente"].astype(str)
        suporte = alvo.value_counts().to_dict()
        minimo = 30
        pequenas = {k: v for k, v in suporte.items() if v < minimo}
        rel.add("M404",
                f"Cada classe do alvo tem suporte minimo de {minimo} registros elegiveis.",
                "aviso", FALHOU if pequenas else PASSOU, len(alvo), len(pequenas),
                exemplos=[f"{k}={v}" for k, v in pequenas.items()],
                detalhe=f"suporte por classe: {suporte}")
        rel.add("M405", "Distribuicao das classes entre os registros elegiveis.",
                "informativo", PASSOU, len(alvo), 0, detalhe=str(suporte))
    else:
        for rid in ("M402", "M403", "M404"):
            rel.add(rid, "Regras de elegibilidade para o modelo.", "critico",
                    NAO_VERIFICADA, detalhe="colunas ausentes")


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Valida a base limpa contra o contrato de qualidade, sem corrigi-la."
    )
    ap.add_argument("--arquivo", default=str(DIR_PROC / "prf_limpo.csv"))
    ap.add_argument("--contrato", default=str(ARQ_CONTRATO))
    ap.add_argument("--saida", default=str(DIR_REPORTS))
    ap.add_argument("--sem-reconciliacao", action="store_true",
                    help="Nao tenta reconciliar com reports/limpeza.json (uso em testes).")
    ap.add_argument("--silencioso", action="store_true")
    args = ap.parse_args(argv)

    try:
        garantir_pastas()
        contrato = carregar_contrato(Path(args.contrato))
        arquivo = Path(args.arquivo)
        dir_saida = Path(args.saida)
        dir_saida.mkdir(parents=True, exist_ok=True)

        if not arquivo.exists():
            print(f"[ERRO OPERACIONAL] Arquivo nao encontrado: {arquivo}")
            return 2
        if arquivo.stat().st_size == 0:
            print(f"[ERRO OPERACIONAL] Arquivo vazio: {arquivo}")
            return 2

        leitura = contrato["leitura_csv"]
        # dtype=str + na_filter=False: o valor textual original e preservado.
        df = pd.read_csv(
            arquivo, sep=leitura["sep"], encoding=leitura["encoding"], dtype=str,
            keep_default_na=False, na_filter=False, quotechar=leitura.get("quotechar", '"'),
        )
    except Exception as erro:  # falha ao abrir/ler => erro operacional
        print(f"[ERRO OPERACIONAL] {type(erro).__name__}: {erro}")
        return 2

    rel = Relatorio(len(df), contrato["chave_primaria"][0])
    validar_estrutura(df, contrato, rel)
    validar_colunas(df, contrato, rel)
    validar_temporais(df, contrato, rel)
    validar_consistencia(df, contrato, rel)
    validar_reconciliacao_e_elegibilidade(
        df, contrato, rel, checar_reconciliacao=not args.sem_reconciliacao
    )

    status = rel.status_global()
    df_regras = rel.dataframe()

    saida_json = {
        "status_global": status,
        "ambiente": ambiente(),
        "arquivo_validado": {
            "caminho": str(arquivo),
            "sha256": hash_arquivo(arquivo),
            "tamanho_bytes": arquivo.stat().st_size,
            "linhas": int(len(df)),
            "colunas": int(df.shape[1]),
            "leitura_usada": {**leitura, "dtype": "str", "na_filter": False},
        },
        "contrato": {
            "arquivo": str(Path(args.contrato)),
            "versao": contrato["versao_contrato"],
            "data": contrato["data_contrato"],
        },
        "resumo": {
            "regras_avaliadas": len(rel.regras),
            "por_status": rel.contagem_por_status(),
            "criticas_falhadas": [
                r["id"] for r in rel.regras
                if r["severidade"] == "critico" and r["status"] == FALHOU
            ],
            "criticas_nao_verificadas": [
                r["id"] for r in rel.regras
                if r["severidade"] == "critico" and r["status"] == NAO_VERIFICADA
            ],
        },
        "ressalvas": rel.ressalvas(),
        "regras": rel.regras,
        "limitacoes_da_auditoria": contrato["limitacoes_da_auditoria"],
        "regras_nao_confirmadas_no_dicionario": contrato["regras_nao_confirmadas"],
        "diferenciacao_importante": {
            "qualidade_da_base": "conformidade com as regras explicitas deste contrato",
            "elegibilidade_para_treino": "ter alvo preenchido (regras M402/M403)",
            "suficiencia_de_amostra": "suporte por classe (regra M404); uma base integra pode ser insuficiente para modelar",
        },
    }
    salvar_json(saida_json, dir_saida / "validacao.json")

    # qualidade_antes_depois.csv: "antes" vem do relatorio da limpeza (se existir),
    # "depois" e medido AQUI, de forma independente, sobre o CSV reaberto.
    exportar_qualidade_antes_depois(df, dir_saida)
    escrever_markdown_validacao(saida_json, df_regras, dir_saida / "validacao.md")
    df_regras.to_csv(dir_saida / "validacao_regras.csv", sep=";", index=False,
                     encoding="utf-8-sig")

    if not args.silencioso:
        print("=" * 72)
        print(f"Arquivo validado : {arquivo}")
        print(f"Linhas x colunas : {len(df)} x {df.shape[1]}")
        print(f"Contrato         : versao {contrato['versao_contrato']}")
        print(f"Regras avaliadas : {len(rel.regras)} -> {rel.contagem_por_status()}")
        print(f"STATUS GLOBAL    : {status}")
        for r in rel.regras:
            if r["status"] == FALHOU and r["severidade"] == "critico":
                print(f"  [CRITICA FALHOU] {r['id']}: {r['descricao']} "
                      f"({r['violacoes']} violacoes)")
        for r in rel.regras:
            if r["status"] == NAO_VERIFICADA and r["severidade"] == "critico":
                print(f"  [CRITICA NAO VERIFICADA] {r['id']}: {r['detalhe']}")
        if rel.ressalvas():
            print("  Ressalvas:")
            for t in rel.ressalvas():
                print(f"    - {t}")
        print(f"Relatorios       : {dir_saida}")
        print("=" * 72)

    return 0 if status in ("APROVADA", "APROVADA_COM_RESSALVAS") else 1


def exportar_qualidade_antes_depois(df: pd.DataFrame, dir_saida: Path) -> None:
    """Compara a base bruta (relatorio do diagnostico) com o que foi medido aqui."""
    import json

    antes = {}
    diag = DIR_REPORTS / "diagnostico.json"
    if diag.exists():
        d = json.loads(diag.read_text(encoding="utf-8"))
        antes = {
            "linhas": d["forma"]["linhas"],
            "colunas": d["forma"]["colunas"],
            "unidade": "pessoa x causa x tipo de acidente",
            "ids_distintos": d["unidade_da_linha"]["ids_de_acidente_distintos"],
            "duplicatas_exatas": d["duplicatas"]["linhas_identicas_excedentes"],
            "total de mortos somando a coluna diretamente": d["somas_de_vitimas"]["soma_ingenua_todas_as_linhas"]["mortos"],
            "total de mortos contando pessoas distintas (valor correto)": d["somas_de_vitimas"]["soma_deduplicada_por_id_pesid"]["mortos"],
        }

    vazias = {c: int((df[c].astype(str) == "").sum()) for c in df.columns}
    depois = {
        "linhas": len(df),
        "colunas": int(df.shape[1]),
        "unidade": "ocorrencia de acidente",
        "ids_distintos": int(df["id"].nunique()) if "id" in df.columns else None,
        "duplicatas_exatas": int(df.duplicated().sum()),
        # Na base limpa as duas medidas coincidem: cada linha e uma ocorrencia, e
        # qtd_mortos ja foi calculado sobre pessoas distintas. E exatamente esse o
        # ganho da agregacao: somar a coluna direto agora da o numero certo.
        "total de mortos somando a coluna diretamente": (
            int(como_inteiro(df["qtd_mortos"].astype(str)).sum())
            if "qtd_mortos" in df.columns else None
        ),
        "total de mortos contando pessoas distintas (valor correto)": (
            int(como_inteiro(df["qtd_mortos"].astype(str)).sum())
            if "qtd_mortos" in df.columns else None
        ),
    }

    linhas = [
        {"metrica": k, "antes_base_bruta": antes.get(k, "nao disponivel"),
         "depois_base_limpa": depois.get(k)}
        for k in depois
    ]
    linhas.append({"metrica": "celulas vazias por coluna (total)",
                   "antes_base_bruta": "ver reports/diagnostico_colunas.csv",
                   "depois_base_limpa": sum(vazias.values())})
    for coluna, n in vazias.items():
        if n:
            linhas.append({"metrica": f"celulas vazias em {coluna}",
                           "antes_base_bruta": "ver diagnostico", "depois_base_limpa": n})
    pd.DataFrame(linhas).to_csv(dir_saida / "qualidade_antes_depois.csv", sep=";",
                                index=False, encoding="utf-8-sig")


def escrever_markdown_validacao(saida: dict, df_regras: pd.DataFrame, caminho: Path) -> None:
    a = saida["arquivo_validado"]
    L = ["# Relatorio de validacao da base limpa\n"]
    L.append(f"**STATUS GLOBAL: {saida['status_global']}**\n")
    L.append(f"- Arquivo validado: `{a['caminho']}`")
    L.append(f"- SHA-256: `{a['sha256']}`")
    L.append(f"- Linhas x colunas: {a['linhas']} x {a['colunas']}")
    L.append(f"- Contrato: `{saida['contrato']['arquivo']}` versao "
             f"{saida['contrato']['versao']} ({saida['contrato']['data']})")
    L.append(f"- Data da execucao: {saida['ambiente']['executado_em']}")
    L.append(f"- Versoes: Python {saida['ambiente']['python']}, "
             f"pandas {saida['ambiente']['pandas']}, "
             f"scikit-learn {saida['ambiente']['scikit_learn']}\n")
    L.append("## Resumo\n")
    L.append(f"- Regras avaliadas: {saida['resumo']['regras_avaliadas']}")
    L.append(f"- Por status: {saida['resumo']['por_status']}")
    L.append(f"- Criticas que falharam: {saida['resumo']['criticas_falhadas'] or 'nenhuma'}")
    L.append(f"- Criticas nao verificadas: {saida['resumo']['criticas_nao_verificadas'] or 'nenhuma'}\n")
    L.append("### Ressalvas\n")
    if saida["ressalvas"]:
        for t in saida["ressalvas"]:
            L.append(f"- {t}")
    else:
        L.append("- Nenhuma.")
    L.append("")
    L.append("## Tres coisas diferentes\n")
    for k, v in saida["diferenciacao_importante"].items():
        L.append(f"- **{k}**: {v}")
    L.append("")
    L.append("## Regras avaliadas\n")
    L.append(tabela_markdown(
        df_regras[["id", "descricao", "severidade", "status", "linhas_avaliadas",
                   "violacoes", "pct_violacoes"]]
    ))
    L.append("\n## Evidencias das regras que nao passaram\n")
    ruins = df_regras[df_regras["status"].isin([FALHOU, NAO_VERIFICADA])]
    if ruins.empty:
        L.append("_Todas as regras aplicaveis passaram._")
    else:
        for _, r in ruins.iterrows():
            L.append(f"### {r['id']} ({r['severidade']} / {r['status']})\n")
            L.append(f"{r['descricao']}\n")
            L.append(f"- Violacoes: {r['violacoes']} de {r['linhas_avaliadas']} "
                     f"({r['pct_violacoes']}%)")
            if r["detalhe"]:
                L.append(f"- Detalhe: {r['detalhe']}")
            if r["exemplos"]:
                L.append(f"- Exemplos: {r['exemplos']}")
            L.append("")
    L.append("## Regras ainda nao confirmadas pelo dicionario\n")
    for t in saida["regras_nao_confirmadas_no_dicionario"]:
        L.append(f"- {t}")
    L.append("\n## Limitacoes desta auditoria\n")
    for t in saida["limitacoes_da_auditoria"]:
        L.append(f"- {t}")
    L.append("\n> Aprovacao significa conformidade com as regras escritas no contrato. "
             "Nao significa que a base esteja '100% limpa', e ausencia de nulos nao e "
             "prova de qualidade.\n")
    caminho.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
