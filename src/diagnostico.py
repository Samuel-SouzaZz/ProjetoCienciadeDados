r"""
diagnostico.py - ETAPA 1: entender o arquivo ANTES de limpar qualquer coisa.

Regra didatica desta etapa: nada e corrigido aqui. Todas as colunas sao lidas como
TEXTO (dtype=str) para que erros de formato aparecam em vez de serem escondidos por
uma conversao automatica do pandas.

O que o script responde:
  1. Quantas linhas e colunas existem? Quais colunas o dicionario previa e faltam?
  2. Qual e a UNIDADE de cada linha? (ocorrencia, pessoa, veiculo, causa, tipo?)
  3. Quantas ausencias por coluna, e com quais tokens ("NA", "(null)", "Nao Informado")?
  4. Quais categorias realmente existem em cada coluna categorica, e com que frequencia?
  5. Quantas linhas sao duplicatas EXATAS?
  6. Existem conflitos de chave: o mesmo 'id' de acidente com valores diferentes em
     colunas que deveriam ser da ocorrencia (data, UF, gravidade...)?
  7. Quais valores falham ao converter para data, hora, inteiro ou decimal?
  8. Qual e o periodo real coberto?

Saidas: reports/diagnostico.json, reports/diagnostico.md,
        reports/diagnostico_categorias.csv, reports/diagnostico_colunas.csv

Uso:
  python src\diagnostico.py
  python src\diagnostico.py --entrada data\raw\acidentes2025_todas_causas_tipos.csv
"""

from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

import pandas as pd

from comum import (
    DIR_RAW,
    DIR_REPORTS,
    LEITURA_BRUTO,
    NOME_CSV_BRUTO,
    TOKENS_AUSENCIA,
    ambiente,
    garantir_pastas,
    hash_arquivo,
    salvar_json,
    tabela_markdown,
)

# ---------------------------------------------------------------------------
# 37 variaveis previstas pelo dicionario oficial da PRF (dados por pessoa, com
# todas as causas e tipos, registros a partir de 2017). Duas variaveis aparecem
# no dicionario com acento/grafia diferente do arquivo; isso e verificado abaixo.
# ---------------------------------------------------------------------------
COLUNAS_DICIONARIO = [
    "id", "pesid", "data_inversa", "dia_semana", "horario", "uf", "br", "km",
    "municipio", "causa_principal", "causa_acidente", "ordem_tipo_acidente",
    "tipo_acidente", "classificacao_acidente", "fase_dia", "sentido_via",
    "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
    "id_veiculo", "tipo_veiculo", "marca", "ano_fabricacao_veiculo",
    "tipo_envolvido", "estado_fisico", "idade", "sexo", "ilesos",
    "feridos_leves", "feridos_graves", "mortos", "latitude", "longitude",
    "regional", "delegacia", "uop",
]

# Grafia do dicionario (com acento) -> grafia real esperada no CSV.
# Registrado explicitamente para nao parecer que "faltam colunas".
DIVERGENCIAS_GRAFIA_DICIONARIO = {
    "classifica??o_acidente": "classificacao_acidente",
    "condi??o_meteorologica": "condicao_metereologica",
}

# Nivel a que cada coluna pertence. Base para descobrir a unidade da linha e para
# saber o que pode ser agregado por ocorrencia sem somar valores repetidos.
NIVEL_COLUNA = {
    "ocorrencia": [
        "id", "data_inversa", "dia_semana", "horario", "uf", "br", "km",
        "municipio", "classificacao_acidente", "fase_dia", "sentido_via",
        "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
        "latitude", "longitude", "regional", "delegacia", "uop",
    ],
    "pessoa": [
        "pesid", "tipo_envolvido", "estado_fisico", "idade", "sexo",
        "ilesos", "feridos_leves", "feridos_graves", "mortos",
    ],
    "veiculo": ["id_veiculo", "tipo_veiculo", "marca", "ano_fabricacao_veiculo"],
    "causa": ["causa_principal", "causa_acidente"],
    "tipo_evento": ["ordem_tipo_acidente", "tipo_acidente"],
}

# Colunas categoricas cuja lista completa de valores queremos ver.
CATEGORICAS = [
    "dia_semana", "uf", "causa_principal", "classificacao_acidente", "fase_dia",
    "sentido_via", "condicao_metereologica", "tipo_pista", "tracado_via",
    "uso_solo", "tipo_veiculo", "tipo_envolvido", "estado_fisico", "sexo",
    "ilesos", "feridos_leves", "feridos_graves", "mortos",
    "ordem_tipo_acidente", "tipo_acidente", "causa_acidente", "regional",
]

# Tokens textuais que a PRF usa para "informacao nao coletada". Nao sao nulos
# do CSV: sao categorias que significam ausencia. Precisam ser contados.
TOKENS_TEXTO_AUSENCIA = ["N?o Informado", "(null)", "Ignorado", "Inv?lido", "N?o Informada"]

RE_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_DATA_BR = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_HORA = re.compile(r"^\d{2}:\d{2}:\d{2}$")
RE_INTEIRO = re.compile(r"^-?\d+$")
RE_DECIMAL_VIRGULA = re.compile(r"^-?\d+(,\d+)?$")

TAMANHO_BLOCO = 200_000


def contar_bloco(bloco: pd.DataFrame, acc: dict) -> None:
    """Acumula as estatisticas de UM bloco de linhas no dicionario 'acc'."""
    acc["linhas"] += len(bloco)

    for coluna in bloco.columns:
        serie = bloco[coluna]
        # Ausencia "de verdade": celula vazia no CSV ou token mapeado na leitura.
        acc["nulos"][coluna] += int(serie.isna().sum())
        # Ausencia "disfarcada de categoria".
        texto = serie.dropna().astype(str)
        for token in TOKENS_TEXTO_AUSENCIA:
            n = int((texto == token).sum())
            if n:
                acc["tokens_texto"][(coluna, token)] += n
        # Espacos sobrando nas pontas (problema de padronizacao).
        acc["espacos_borda"][coluna] += int((texto != texto.str.strip()).sum())
        acc["nao_nulos"][coluna] += int(len(texto))

    for coluna in CATEGORICAS:
        if coluna in bloco.columns:
            acc["categorias"][coluna].update(bloco[coluna].fillna("<AUSENTE>").astype(str))

    # ---- duplicatas exatas: guarda o hash da linha inteira, nao a linha ----
    concat = bloco.fillna("\x00").astype(str).agg("\x01".join, axis=1)
    for h in pd.util.hash_pandas_object(concat, index=False):
        acc["hashes_linha"][int(h)] += 1

    # ---- unidade da linha: id, (id,pesid), (id,pesid,causa,ordem_tipo) ----
    acc["ids"].update(bloco["id"].dropna().astype(str))
    acc["pares_id_pesid"].update(
        zip(bloco["id"].astype(str), bloco["pesid"].fillna("<AUSENTE>").astype(str))
    )
    acc["quadras"].update(
        zip(
            bloco["id"].astype(str),
            bloco["pesid"].fillna("<AUSENTE>").astype(str),
            bloco["causa_acidente"].fillna("<AUSENTE>").astype(str),
            bloco["ordem_tipo_acidente"].fillna("<AUSENTE>").astype(str),
        )
    )

    # ---- erros de conversao (formato) ----
    def falhas(coluna, regex):
        if coluna not in bloco.columns:
            return
        texto = bloco[coluna].dropna().astype(str).str.strip()
        ruins = texto[~texto.str.match(regex)]
        acc["formato_invalido"][coluna] += int(len(ruins))
        for v in ruins.head(5):
            if len(acc["exemplos_formato"][coluna]) < 5:
                acc["exemplos_formato"][coluna].append(v)

    falhas("data_inversa", RE_DATA_ISO)
    falhas("horario", RE_HORA)
    for c in ("id", "pesid", "br", "id_veiculo", "ano_fabricacao_veiculo",
              "idade", "ordem_tipo_acidente", "ilesos", "feridos_leves",
              "feridos_graves", "mortos"):
        falhas(c, RE_INTEIRO)
    for c in ("km", "latitude", "longitude"):
        falhas(c, RE_DECIMAL_VIRGULA)

    # Formato de data: ISO (aaaa-mm-dd) ou brasileiro (dd/mm/aaaa)?
    d = bloco["data_inversa"].dropna().astype(str).str.strip()
    acc["data_formato"]["iso"] += int(d.str.match(RE_DATA_ISO).sum())
    acc["data_formato"]["br"] += int(d.str.match(RE_DATA_BR).sum())
    if len(d):
        acc["data_min"] = d.min() if acc["data_min"] is None else min(acc["data_min"], d.min())
        acc["data_max"] = d.max() if acc["data_max"] is None else max(acc["data_max"], d.max())

    # Idade -1 = codigo de ausencia segundo o dicionario (NAO e idade negativa real).
    if "idade" in bloco.columns:
        idade = pd.to_numeric(bloco["idade"], errors="coerce")
        acc["idade_menos_um"] += int((idade == -1).sum())
        acc["idade_negativa_outra"] += int(((idade < 0) & (idade != -1)).sum())


def conflitos_de_chave(caminho: Path) -> dict:
    """Verifica se colunas de OCORRENCIA variam dentro do mesmo 'id'.

    Se variarem, o arquivo nao pode ser agregado por ocorrencia sem revisao.
    Le apenas as colunas necessarias, para caber na memoria.
    """
    colunas = [c for c in NIVEL_COLUNA["ocorrencia"]]
    df = pd.read_csv(
        caminho, usecols=colunas, dtype=str, na_values=TOKENS_AUSENCIA,
        keep_default_na=True, **LEITURA_BRUTO,
    )
    resultado = {"ocorrencias": int(df["id"].nunique(dropna=False)), "colunas": {}}
    grupos = df.groupby("id", dropna=False)
    for coluna in colunas:
        if coluna == "id":
            continue
        n_distintos = grupos[coluna].nunique(dropna=True)
        conflitantes = n_distintos[n_distintos > 1]
        resultado["colunas"][coluna] = {
            "ids_com_mais_de_um_valor": int(len(conflitantes)),
            "exemplos_id": [str(i) for i in conflitantes.index[:5]],
        }
    # Contagens por pessoa: sao binarias por pessoa, mas a linha esta repetida
    # por causa/tipo. Mostrar a diferenca entre somar tudo e somar por pessoa.
    return resultado


def soma_ingenua_versus_por_pessoa(caminho: Path) -> dict:
    """Demonstra o erro de somar 'mortos' sem deduplicar por pessoa.

    A linha do arquivo esta repetida para cada causa e cada tipo de acidente.
    Somar a coluna diretamente multiplica os mortos. Este numero e a prova.
    """
    df = pd.read_csv(
        caminho, usecols=["id", "pesid", "mortos", "feridos_leves", "feridos_graves", "ilesos"],
        dtype=str, na_values=TOKENS_AUSENCIA, **LEITURA_BRUTO,
    )
    for c in ("mortos", "feridos_leves", "feridos_graves", "ilesos"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    ingenua = {c: int(df[c].sum()) for c in ("mortos", "feridos_leves", "feridos_graves", "ilesos")}
    unico = df.drop_duplicates(subset=["id", "pesid"])
    por_pessoa = {c: int(unico[c].sum()) for c in ("mortos", "feridos_leves", "feridos_graves", "ilesos")}
    return {
        "soma_ingenua_todas_as_linhas": ingenua,
        "soma_deduplicada_por_id_pesid": por_pessoa,
        "linhas_totais": int(len(df)),
        "linhas_distintas_id_pesid": int(len(unico)),
        "observacao": (
            "A soma ingenua superestima porque cada pessoa aparece repetida uma vez "
            "por combinacao de causa e tipo de acidente."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnostico da base bruta da PRF.")
    ap.add_argument("--entrada", default=str(DIR_RAW / NOME_CSV_BRUTO))
    ap.add_argument("--bloco", type=int, default=TAMANHO_BLOCO)
    args = ap.parse_args()

    garantir_pastas()
    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"[ERRO] Arquivo nao encontrado: {entrada}")
        print("Coloque o CSV da PRF em data\\raw\\ e rode de novo.")
        return 2

    print(f"[1/4] Lendo {entrada.name} em blocos de {args.bloco} linhas...")
    acc = {
        "linhas": 0,
        "nulos": collections.Counter(),
        "nao_nulos": collections.Counter(),
        "tokens_texto": collections.Counter(),
        "espacos_borda": collections.Counter(),
        "categorias": collections.defaultdict(collections.Counter),
        "hashes_linha": collections.Counter(),
        "ids": set(),
        "pares_id_pesid": set(),
        "quadras": set(),
        "formato_invalido": collections.Counter(),
        "exemplos_formato": collections.defaultdict(list),
        "data_formato": collections.Counter(),
        "data_min": None,
        "data_max": None,
        "idade_menos_um": 0,
        "idade_negativa_outra": 0,
    }

    colunas_arquivo = None
    leitor = pd.read_csv(
        entrada, dtype=str, na_values=TOKENS_AUSENCIA, keep_default_na=True,
        chunksize=args.bloco, **LEITURA_BRUTO,
    )
    for i, bloco in enumerate(leitor, 1):
        if colunas_arquivo is None:
            colunas_arquivo = list(bloco.columns)
        contar_bloco(bloco, acc)
        print(f"      bloco {i}: {acc['linhas']:,} linhas lidas".replace(",", "."))

    print("[2/4] Verificando conflitos de chave por ocorrencia...")
    conflitos = conflitos_de_chave(entrada)

    print("[3/4] Comparando soma ingenua x soma deduplicada por pessoa...")
    somas = soma_ingenua_versus_por_pessoa(entrada)

    print("[4/4] Escrevendo relatorios...")
    duplicatas_exatas = int(sum(n - 1 for n in acc["hashes_linha"].values() if n > 1))
    grupos_duplicados = int(sum(1 for n in acc["hashes_linha"].values() if n > 1))

    faltando = [c for c in COLUNAS_DICIONARIO if c not in colunas_arquivo]
    extras = [c for c in colunas_arquivo if c not in COLUNAS_DICIONARIO]

    relatorio = {
        "ambiente": ambiente(),
        "arquivo": {
            "caminho": str(entrada),
            "tamanho_bytes": entrada.stat().st_size,
            "sha256": hash_arquivo(entrada),
            "configuracao_leitura": LEITURA_BRUTO,
            "tokens_ausencia_na_leitura": TOKENS_AUSENCIA,
        },
        "forma": {
            "linhas": acc["linhas"],
            "colunas": len(colunas_arquivo),
            "nomes_colunas": colunas_arquivo,
            "nomes_duplicados": [
                c for c, n in collections.Counter(colunas_arquivo).items() if n > 1
            ],
        },
        "conformidade_com_dicionario": {
            "colunas_do_dicionario_ausentes_no_arquivo": faltando,
            "colunas_no_arquivo_fora_do_dicionario": extras,
            "divergencias_de_grafia_esperadas": DIVERGENCIAS_GRAFIA_DICIONARIO,
        },
        "unidade_da_linha": {
            "linhas": acc["linhas"],
            "ids_de_acidente_distintos": len(acc["ids"]),
            "pares_id_pesid_distintos": len(acc["pares_id_pesid"]),
            "combinacoes_id_pesid_causa_ordemtipo_distintas": len(acc["quadras"]),
            "linhas_por_ocorrencia_media": (
                round(acc["linhas"] / len(acc["ids"]), 3) if acc["ids"] else None
            ),
        },
        "duplicatas": {
            "linhas_identicas_excedentes": duplicatas_exatas,
            "grupos_com_linhas_identicas": grupos_duplicados,
        },
        "conflitos_de_chave_por_id": conflitos,
        "somas_de_vitimas": somas,
        "datas": {
            "formato_iso_aaaa_mm_dd": int(acc["data_formato"]["iso"]),
            "formato_br_dd_mm_aaaa": int(acc["data_formato"]["br"]),
            "minima_texto": acc["data_min"],
            "maxima_texto": acc["data_max"],
            "observacao_dicionario": (
                "O dicionario descreve data_inversa como dd/mm/aaaa; verificar acima "
                "qual formato o arquivo realmente usa."
            ),
        },
        "idade": {
            "valores_iguais_a_-1_codigo_de_ausencia": acc["idade_menos_um"],
            "valores_negativos_diferentes_de_-1": acc["idade_negativa_outra"],
        },
    }

    # --- tabela por coluna ---
    linhas_col = []
    for coluna in colunas_arquivo:
        nivel = next((n for n, cs in NIVEL_COLUNA.items() if coluna in cs), "nao_classificado")
        nulos = int(acc["nulos"][coluna])
        linhas_col.append(
            {
                "coluna": coluna,
                "nivel": nivel,
                "nao_nulos": int(acc["nao_nulos"][coluna]),
                "nulos": nulos,
                "pct_nulos": round(100 * nulos / acc["linhas"], 4) if acc["linhas"] else 0.0,
                "valores_distintos": len(acc["categorias"][coluna]) if coluna in CATEGORICAS else "",
                "formato_invalido": int(acc["formato_invalido"][coluna]),
                "exemplos_formato_invalido": " | ".join(acc["exemplos_formato"][coluna]),
                "com_espaco_nas_bordas": int(acc["espacos_borda"][coluna]),
                "tokens_texto_de_ausencia": "; ".join(
                    f"{t}={n}" for (c, t), n in acc["tokens_texto"].items() if c == coluna
                ),
            }
        )
    df_col = pd.DataFrame(linhas_col)
    df_col.to_csv(DIR_REPORTS / "diagnostico_colunas.csv", sep=";", index=False, encoding="utf-8-sig")

    # --- tabela de categorias ---
    linhas_cat = []
    for coluna, cont in acc["categorias"].items():
        for valor, n in cont.most_common():
            linhas_cat.append(
                {
                    "coluna": coluna,
                    "valor": valor,
                    "frequencia": int(n),
                    "pct": round(100 * n / acc["linhas"], 4),
                }
            )
    pd.DataFrame(linhas_cat).to_csv(
        DIR_REPORTS / "diagnostico_categorias.csv", sep=";", index=False, encoding="utf-8-sig"
    )

    relatorio["categorias_resumo"] = {
        coluna: {
            "distintos": len(cont),
            "top10": dict(cont.most_common(10)),
        }
        for coluna, cont in acc["categorias"].items()
    }

    salvar_json(relatorio, DIR_REPORTS / "diagnostico.json")
    escrever_markdown(relatorio, df_col, DIR_REPORTS / "diagnostico.md")

    print()
    print("=" * 72)
    print(f"Linhas: {acc['linhas']:,}".replace(",", "."))
    print(f"Colunas: {len(colunas_arquivo)}")
    print(f"IDs de acidente distintos: {len(acc['ids']):,}".replace(",", "."))
    print(f"Pares id+pesid distintos: {len(acc['pares_id_pesid']):,}".replace(",", "."))
    print(f"Duplicatas exatas (linhas excedentes): {duplicatas_exatas:,}".replace(",", "."))
    print(f"Periodo (texto): {acc['data_min']} a {acc['data_max']}")
    print(f"Relatorios em: {DIR_REPORTS}")
    print("=" * 72)
    return 0


def escrever_markdown(rel: dict, df_col: pd.DataFrame, caminho: Path) -> None:
    u = rel["unidade_da_linha"]
    L = []
    L.append("# Diagnostico da base bruta da PRF\n")
    L.append(f"- Arquivo: `{rel['arquivo']['caminho']}`")
    L.append(f"- SHA-256: `{rel['arquivo']['sha256']}`")
    L.append(f"- Execucao: {rel['ambiente']['executado_em']}")
    L.append(f"- Leitura: separador `{LEITURA_BRUTO['sep']}`, encoding `{LEITURA_BRUTO['encoding']}`, "
             f"decimal `{LEITURA_BRUTO['decimal']}`\n")
    L.append("## 1. Forma\n")
    L.append(f"- Linhas: **{rel['forma']['linhas']}**")
    L.append(f"- Colunas: **{rel['forma']['colunas']}**")
    L.append(f"- Nomes duplicados: {rel['forma']['nomes_duplicados'] or 'nenhum'}\n")
    L.append("## 2. Unidade de cada linha\n")
    L.append(f"- Linhas: {u['linhas']}")
    L.append(f"- IDs de acidente distintos: {u['ids_de_acidente_distintos']}")
    L.append(f"- Pares (id, pesid) distintos: {u['pares_id_pesid_distintos']}")
    L.append(f"- Combinacoes (id, pesid, causa, ordem_tipo) distintas: "
             f"{u['combinacoes_id_pesid_causa_ordemtipo_distintas']}")
    L.append(f"- Media de linhas por ocorrencia: {u['linhas_por_ocorrencia_media']}\n")
    L.append("> Como as linhas por ocorrencia sao muitas, o arquivo NAO esta na unidade "
             "'uma linha = um acidente'. Agregar por `id` e obrigatorio antes da analise "
             "por ocorrencia, e `id` repetido NAO significa duplicata.\n")
    L.append("## 3. Somas de vitimas: ingenua x deduplicada\n")
    s = rel["somas_de_vitimas"]
    L.append("| medida | soma de todas as linhas | soma por (id, pesid) |")
    L.append("|---|---|---|")
    for k in s["soma_ingenua_todas_as_linhas"]:
        L.append(f"| {k} | {s['soma_ingenua_todas_as_linhas'][k]} | {s['soma_deduplicada_por_id_pesid'][k]} |")
    L.append(f"\n{s['observacao']}\n")
    L.append("## 4. Duplicatas exatas\n")
    L.append(f"- Linhas identicas excedentes: {rel['duplicatas']['linhas_identicas_excedentes']}")
    L.append(f"- Grupos com linhas identicas: {rel['duplicatas']['grupos_com_linhas_identicas']}\n")
    L.append("## 5. Conflitos de chave (colunas de ocorrencia que variam dentro do mesmo id)\n")
    L.append("| coluna | ids com mais de um valor | exemplos |")
    L.append("|---|---|---|")
    for c, d in rel["conflitos_de_chave_por_id"]["colunas"].items():
        L.append(f"| {c} | {d['ids_com_mais_de_um_valor']} | {', '.join(d['exemplos_id']) or '-'} |")
    L.append("")
    L.append("## 6. Datas\n")
    d = rel["datas"]
    L.append(f"- Em formato ISO `aaaa-mm-dd`: {d['formato_iso_aaaa_mm_dd']}")
    L.append(f"- Em formato `dd/mm/aaaa`: {d['formato_br_dd_mm_aaaa']}")
    L.append(f"- Periodo textual: {d['minima_texto']} a {d['maxima_texto']}")
    L.append(f"- {d['observacao_dicionario']}\n")
    L.append("## 7. Conformidade com o dicionario\n")
    cf = rel["conformidade_com_dicionario"]
    L.append(f"- Colunas do dicionario ausentes no arquivo: "
             f"{cf['colunas_do_dicionario_ausentes_no_arquivo'] or 'nenhuma'}")
    L.append(f"- Colunas no arquivo fora do dicionario: "
             f"{cf['colunas_no_arquivo_fora_do_dicionario'] or 'nenhuma'}")
    L.append("- Divergencias de grafia entre dicionario e arquivo: "
             + ", ".join(f"`{a}` -> `{b}`" for a, b in cf["divergencias_de_grafia_esperadas"].items()))
    L.append("")
    L.append("## 8. Panorama por coluna\n")
    L.append(tabela_markdown(df_col))
    L.append("\n## 9. Categorias observadas\n")
    for coluna, info in rel["categorias_resumo"].items():
        L.append(f"### {coluna} ({info['distintos']} valores distintos)\n")
        for v, n in info["top10"].items():
            L.append(f"- `{v}`: {n}")
        L.append("")
    L.append("\n> Observado no arquivo nao e o mesmo que permitido pelo dicionario. "
             "As categorias validas sao fixadas em `config/regras_qualidade.json`.\n")
    caminho.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
