r"""
limpeza.py - ETAPA 2 e 3 do KDD: pre-processamento e transformacao.

O que este script faz, em ordem, e por que:

  PASSO 1 - Leitura controlada
      Le o CSV bruto com separador ';', encoding latin-1 e decimal ','.
      TODAS as colunas entram como texto. Nada de conversao automatica: se um
      valor estiver malformado, queremos ve-lo, nao deixar o pandas adivinhar.

  PASSO 2 - Normalizacao de cabecalhos
      Confere se algum nome de coluna mudou de forma e se ha colisao de nomes.
      Registra o mapa nome_original -> nome_padronizado.

  PASSO 3 - Limpeza de texto
      Remove espacos duplicados e caracteres invisiveis. NAO mexe em acentos nem
      em maiusculas: os rotulos legiveis em portugues precisam sobreviver.

  PASSO 4 - Tokens de ausencia por coluna
      "Ignorado" em condicao_metereologica, "Nao Informado" em sentido_via,
      "NA/NA" em marca, "0" em ano_fabricacao_veiculo. Cada conversao e auditada.
      Nao existe fillna(0) global.

  PASSO 5 - Padronizacao de categorias por mapeamento EXPLICITO
      dia_semana 'sabado' -> 'Sabado'; uso_solo 'Sim' -> 'Urbano' (autorizado pelo
      dicionario); fase_dia 'Pleno dia' -> 'Pleno Dia'; tracado_via multivalorado
      passa a ter componentes em ordem alfabetica.

  PASSO 6 - Revisao de campos impossiveis
      idade fora de 0..120 vira ausencia, com copia do registro original em
      data/quarantine/campos_para_revisao.csv. O valor original NUNCA e perdido.

  PASSO 7 - Verificacao de integridade da chave
      Confere se as colunas de ocorrencia sao constantes dentro de cada 'id'.
      Se houver conflito, a ocorrencia inteira vai para quarentena, nao para a base.

  PASSO 8 - Agregacao para a unidade OCORRENCIA
      Este e o ponto critico. O arquivo bruto repete cada pessoa uma vez por
      combinacao de causa e tipo. Somar 'mortos' direto multiplicaria os obitos.
      Por isso as contagens sao feitas sobre pares (id, pesid) DISTINTOS, e os
      veiculos sobre pares (id, id_veiculo) DISTINTOS.

  PASSO 9 - Atributos derivados
      ano, mes, mes_nome, hora, faixa_horaria, fim_de_semana, dia_semana_calculado.

  PASSO 10 - Sinalizacao de elegibilidade
      Alvo ausente nao e imputado nem apagado: fica na base com alvo_ausente=Sim
      e elegivel_modelo=Nao.

  PASSO 11 - Exportacao e reconciliacao
      prf_limpo.csv (ocorrencia), prf_pessoas.csv (pessoa), esquema de leitura,
      auditoria, quarentena, qualidade antes/depois e reconciliacao das linhas.

Uso:
  python src\limpeza.py
  python src\limpeza.py --entrada data\raw\acidentes2025_todas_causas_tipos.csv --amostra 50000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from comum import (
    DIR_PROC,
    DIR_QUAR,
    DIR_RAW,
    DIR_REPORTS,
    ESCRITA_LIMPO,
    LEITURA_BRUTO,
    NOME_CSV_BRUTO,
    TOKENS_AUSENCIA,
    Auditoria,
    ambiente,
    carregar_contrato,
    chave_comparacao,
    garantir_pastas,
    hash_arquivo,
    limpar_texto,
    salvar_json,
    tabela_markdown,
)

# ---------------------------------------------------------------------------
# PASSO 2 - mapa de cabecalhos. O arquivo da PRF ja usa nomes minusculos com
# underscore, entao a padronizacao aqui e quase identidade. O mapa existe para
# ficar documentado e para o caso de a PRF mudar a grafia em outra versao.
# ---------------------------------------------------------------------------
MAPA_CABECALHOS = {
    "classificação_acidente": "classificacao_acidente",
    "condição_meteorologica": "condicao_metereologica",
    "condicao_meteorologica": "condicao_metereologica",
}

# Colunas que descrevem a OCORRENCIA (devem ser constantes dentro de cada id).
COLS_OCORRENCIA = [
    "data_inversa", "dia_semana", "horario", "uf", "br", "km", "municipio",
    "classificacao_acidente", "fase_dia", "sentido_via", "condicao_metereologica",
    "tipo_pista", "tracado_via", "uso_solo", "latitude", "longitude",
    "regional", "delegacia", "uop",
]

COLS_PESSOA = [
    "pesid", "tipo_envolvido", "estado_fisico", "idade", "sexo",
    "ilesos", "feridos_leves", "feridos_graves", "mortos",
]

# ---------------------------------------------------------------------------
# PASSO 4 - tokens que significam ausencia em colunas ESPECIFICAS.
# ---------------------------------------------------------------------------
TOKENS_POR_COLUNA = {
    "condicao_metereologica": ["Ignorado"],
    "sentido_via": ["Não Informado"],
    "estado_fisico": ["Não Informado"],
    "sexo": ["Não Informado", "Ignorado", "Inválido"],
    "marca": ["NA/NA"],
    "ano_fabricacao_veiculo": ["0"],
}

# ---------------------------------------------------------------------------
# PASSO 5 - mapeamentos explicitos de categorias.
# Cada entrada e uma decisao documentada, nao um "title case" automatico.
# ---------------------------------------------------------------------------
MAPA_DIA_SEMANA = {
    "domingo": "Domingo",
    "segunda-feira": "Segunda-feira",
    "terca-feira": "Terça-feira",
    "quarta-feira": "Quarta-feira",
    "quinta-feira": "Quinta-feira",
    "sexta-feira": "Sexta-feira",
    "sabado": "Sábado",
}

# Autorizado pelo dicionario: "uso_solo: Urbano=Sim; Rural=Nao".
MAPA_USO_SOLO = {"sim": "Urbano", "nao": "Rural"}

# O arquivo mistura 'Pleno dia' com 'Plena Noite'. Padronizamos a capitalizacao.
MAPA_FASE_DIA = {
    "amanhecer": "Amanhecer",
    "pleno dia": "Pleno Dia",
    "anoitecer": "Anoitecer",
    "plena noite": "Plena Noite",
}

MAPA_TIPO_PISTA = {"simples": "Simples", "dupla": "Dupla", "multipla": "Múltipla"}

MAPA_CONDICAO = {
    "ceu claro": "Céu Claro",
    "sol": "Sol",
    "nublado": "Nublado",
    "chuva": "Chuva",
    "garoa/chuvisco": "Garoa/Chuvisco",
    "nevoeiro/neblina": "Nevoeiro/Neblina",
    "vento": "Vento",
    "neve": "Neve",
}

MAPA_SENTIDO = {"crescente": "Crescente", "decrescente": "Decrescente"}

# Componentes atomicos de tracado_via, com a grafia final desejada.
MAPA_TRACADO_COMPONENTE = {
    "aclive": "Aclive",
    "curva": "Curva",
    "declive": "Declive",
    "desvio temporario": "Desvio Temporário",
    "em obras": "Em Obras",
    "intersecao de vias": "Interseção de Vias",
    "ponte": "Ponte",
    "reta": "Reta",
    "retorno regulamentado": "Retorno Regulamentado",
    "rotatoria": "Rotatória",
    "tunel": "Túnel",
    "viaduto": "Viaduto",
}

DIA_SEMANA_POR_INDICE = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira",
    4: "Sexta-feira", 5: "Sábado", 6: "Domingo",
}
MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro",
    12: "Dezembro",
}

IDADE_MINIMA, IDADE_MAXIMA = 0, 120

# Ordem final das colunas do CSV limpo (garante estabilidade entre execucoes).
ORDEM_COLUNAS_OCORRENCIA = [
    "id", "data_inversa", "horario", "dia_semana", "dia_semana_calculado",
    "dia_semana_divergente", "ano", "mes", "mes_nome", "hora", "faixa_horaria",
    "fim_de_semana", "uf", "br", "km", "municipio", "fase_dia", "sentido_via",
    "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
    "classificacao_acidente", "qtd_pessoas", "qtd_ilesos", "qtd_feridos_leves",
    "qtd_feridos_graves", "qtd_feridos", "qtd_mortos",
    "qtd_estado_fisico_nao_informado", "qtd_veiculos", "qtd_causas_distintas",
    "qtd_tipos_distintos", "causa_principal_acidente", "tipo_acidente_principal",
    "latitude", "longitude", "regional", "delegacia", "uop",
    "alvo_ausente", "elegivel_modelo", "motivo_inelegibilidade", "entradas_ausentes",
]


def para_numero(serie: pd.Series) -> pd.Series:
    """Converte texto com decimal ',' para numero, sem quebrar em valor invalido."""
    return pd.to_numeric(
        serie.astype("string").str.replace(",", ".", regex=False), errors="coerce"
    )


def formatar_decimal(serie: pd.Series, casas: int) -> pd.Series:
    """Formata numero como texto com virgula decimal, preservando ausencia."""
    return serie.map(
        lambda v: pd.NA if pd.isna(v) else f"{v:.{casas}f}".replace(".", ",")
    ).astype("string")


def faixa_da_hora(hora: int) -> str:
    """Faixa de RELOGIO (nao confundir com fase_dia registrada pela PRF)."""
    if 0 <= hora <= 5:
        return "Madrugada"
    if 6 <= hora <= 11:
        return "Manhã"
    if 12 <= hora <= 17:
        return "Tarde"
    return "Noite"


def canonizar_tracado(valor) -> object:
    """Ordena e padroniza os componentes de tracado_via.

    'Reta;Declive' e 'Declive;Reta' descrevem o mesmo traçado. Sem essa ordenacao
    o arquivo bruto tem 605 rotulos diferentes para poucas combinacoes reais.
    Componentes desconhecidos sao mantidos como estao, para nao apagar informacao.
    """
    if valor is pd.NA or valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return pd.NA
    partes = {p.strip() for p in str(valor).split(";") if p.strip()}
    if not partes:
        return pd.NA
    padronizadas = {MAPA_TRACADO_COMPONENTE.get(chave_comparacao(p), p) for p in partes}
    return ";".join(sorted(padronizadas))


def aplicar_mapa(
    df: pd.DataFrame, coluna: str, mapa: dict, aud: Auditoria, regra: str
) -> int:
    """Substitui valores usando um mapa EXPLICITO, auditando cada alteracao.

    A comparacao usa a chave sem acento/minuscula, mas o valor gravado e o rotulo
    legivel do mapa. Valores fora do mapa NAO sao alterados: aparecem depois como
    violacao de dominio na validacao, em vez de desaparecerem silenciosamente.
    """
    if coluna not in df.columns:
        return 0
    original = df[coluna]
    novo = original.map(
        lambda v: pd.NA if pd.isna(v) else mapa.get(chave_comparacao(v), v)
    ).astype("string")
    mudou = original.notna() & (original.astype("string") != novo)
    for idx in df.index[mudou][:5000]:
        aud.registrar(
            df.at[idx, "id"], coluna, regra, original.at[idx], novo.at[idx], idx
        )
    df[coluna] = novo
    return int(mudou.sum())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Limpeza e agregacao da base da PRF.")
    ap.add_argument("--entrada", default=str(DIR_RAW / NOME_CSV_BRUTO))
    ap.add_argument(
        "--amostra", type=int, default=0,
        help="Le apenas as N primeiras linhas (para teste rapido). 0 = arquivo inteiro.",
    )
    ap.add_argument(
        "--base-saida", default=None,
        help=(
            "Pasta alternativa para as saidas (cria processed/, quarantine/ e reports/ "
            "dentro dela). Usada pelos testes para nao sobrescrever os arquivos reais."
        ),
    )
    args = ap.parse_args(argv)

    # Redireciona as pastas de saida quando os testes pedem isolamento.
    global DIR_PROC, DIR_QUAR, DIR_REPORTS
    if args.base_saida:
        base = Path(args.base_saida)
        DIR_PROC, DIR_QUAR, DIR_REPORTS = (
            base / "processed", base / "quarantine", base / "reports",
        )
        for d in (DIR_PROC, DIR_QUAR, DIR_REPORTS):
            d.mkdir(parents=True, exist_ok=True)

    garantir_pastas()
    contrato = carregar_contrato()
    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"[ERRO] Arquivo nao encontrado: {entrada}")
        return 2

    aud = Auditoria(entrada.name)
    resumo: dict = {
        "ambiente": ambiente(),
        "versao_contrato": contrato["versao_contrato"],
        "entrada": {
            "caminho": str(entrada),
            "sha256": hash_arquivo(entrada),
            "configuracao_leitura": LEITURA_BRUTO,
        },
        "passos": {},
    }

    # ---------------- PASSO 1: leitura ----------------
    print("[PASSO 1] Lendo o arquivo bruto como texto...")
    leitura = dict(LEITURA_BRUTO)
    bruto = pd.read_csv(
        entrada, dtype=str, na_values=TOKENS_AUSENCIA, keep_default_na=True,
        nrows=args.amostra or None, **leitura,
    )
    n_entrada = len(bruto)
    print(f"          {n_entrada} linhas x {bruto.shape[1]} colunas")
    resumo["passos"]["1_leitura"] = {
        "linhas_lidas": n_entrada,
        "colunas_lidas": int(bruto.shape[1]),
        "linhas_ilegiveis": 0,
        "observacao": "O pandas nao reportou linha ilegivel. Todas as colunas foram lidas como texto.",
    }

    # ---------------- PASSO 2: cabecalhos ----------------
    print("[PASSO 2] Normalizando cabecalhos...")
    originais = list(bruto.columns)
    renomeadas = [MAPA_CABECALHOS.get(c, c) for c in originais]
    colisoes = [c for c in set(renomeadas) if renomeadas.count(c) > 1]
    if colisoes:
        print(f"[ERRO] Colisao de nomes de coluna apos padronizacao: {colisoes}")
        return 1
    bruto.columns = renomeadas
    resumo["passos"]["2_cabecalhos"] = {
        "mapa_original_para_padronizado": dict(zip(originais, renomeadas)),
        "renomeadas": [f"{a} -> {b}" for a, b in zip(originais, renomeadas) if a != b],
        "colisoes": colisoes,
    }

    # Qualidade ANTES (medida sobre o arquivo bruto, ainda sem tratamento).
    antes = {
        "linhas": n_entrada,
        "colunas": int(bruto.shape[1]),
        "nulos_por_coluna": {c: int(bruto[c].isna().sum()) for c in bruto.columns},
        "duplicatas_exatas": int(bruto.duplicated().sum()),
        "ids_distintos": int(bruto["id"].nunique()),
        "valores_distintos_tracado_via": int(bruto["tracado_via"].nunique()),
        "categorias_dia_semana": sorted(bruto["dia_semana"].dropna().unique().tolist()),
        "categorias_uso_solo": sorted(bruto["uso_solo"].dropna().unique().tolist()),
    }

    # ---------------- PASSO 3: limpeza de texto ----------------
    print("[PASSO 3] Removendo espacos extras e caracteres invisiveis...")
    alteracoes_texto = 0
    for coluna in bruto.columns:
        original = bruto[coluna]
        novo = original.map(limpar_texto).astype("string")
        mudou = original.notna() & (original.astype("string") != novo)
        n = int(mudou.sum())
        if n:
            alteracoes_texto += n
            for idx in bruto.index[mudou][:200]:
                aud.registrar(bruto.at[idx, "id"], coluna, "limpeza_texto",
                              original.at[idx], novo.at[idx], idx)
        bruto[coluna] = novo
    resumo["passos"]["3_texto"] = {"celulas_alteradas": alteracoes_texto}

    # ---------------- PASSO 4: tokens de ausencia por coluna ----------------
    print("[PASSO 4] Convertendo tokens de ausencia declarados no contrato...")
    conversoes = {}
    for coluna, tokens in TOKENS_POR_COLUNA.items():
        if coluna not in bruto.columns:
            continue
        alvo = bruto[coluna].isin(tokens)
        n = int(alvo.sum())
        if n:
            for idx in bruto.index[alvo][:500]:
                aud.registrar(bruto.at[idx, "id"], coluna, f"token_ausencia:{tokens}",
                              bruto.at[idx, coluna], None, idx)
            bruto.loc[alvo, coluna] = pd.NA
        conversoes[coluna] = {"tokens": tokens, "celulas_convertidas": n}
    resumo["passos"]["4_tokens_ausencia"] = conversoes

    # ---------------- PASSO 5: categorias ----------------
    print("[PASSO 5] Padronizando categorias por mapeamentos explicitos...")
    padronizacoes = {
        "dia_semana": aplicar_mapa(bruto, "dia_semana", MAPA_DIA_SEMANA, aud, "mapa_dia_semana"),
        "uso_solo": aplicar_mapa(bruto, "uso_solo", MAPA_USO_SOLO, aud, "mapa_uso_solo_dicionario"),
        "fase_dia": aplicar_mapa(bruto, "fase_dia", MAPA_FASE_DIA, aud, "mapa_fase_dia"),
        "tipo_pista": aplicar_mapa(bruto, "tipo_pista", MAPA_TIPO_PISTA, aud, "mapa_tipo_pista"),
        "condicao_metereologica": aplicar_mapa(
            bruto, "condicao_metereologica", MAPA_CONDICAO, aud, "mapa_condicao_metereologica"),
        "sentido_via": aplicar_mapa(bruto, "sentido_via", MAPA_SENTIDO, aud, "mapa_sentido_via"),
    }
    bruto["uf"] = bruto["uf"].str.upper()

    # tracado_via: ordenacao dos componentes
    original_tracado = bruto["tracado_via"]
    novo_tracado = original_tracado.map(canonizar_tracado).astype("string")
    mudou_tracado = original_tracado.notna() & (original_tracado.astype("string") != novo_tracado)
    for idx in bruto.index[mudou_tracado][:2000]:
        aud.registrar(bruto.at[idx, "id"], "tracado_via", "ordenacao_componentes",
                      original_tracado.at[idx], novo_tracado.at[idx], idx)
    # Mapa completo original -> canonico, para o relatorio (uma linha por rotulo).
    mapa_tracado = (
        pd.DataFrame({"original": original_tracado, "canonico": novo_tracado})
        .dropna().drop_duplicates().sort_values("canonico")
    )
    mapa_tracado.to_csv(DIR_REPORTS / "mapa_tracado_via.csv", sep=";",
                        index=False, encoding="utf-8-sig")
    bruto["tracado_via"] = novo_tracado
    padronizacoes["tracado_via_celulas_reordenadas"] = int(mudou_tracado.sum())
    padronizacoes["tracado_via_rotulos_antes"] = int(original_tracado.nunique())
    padronizacoes["tracado_via_rotulos_depois"] = int(novo_tracado.nunique())
    resumo["passos"]["5_categorias"] = padronizacoes

    # ---------------- PASSO 6: campos impossiveis ----------------
    print("[PASSO 6] Revisando campos com valores impossiveis...")
    revisao = []
    idade_num = para_numero(bruto["idade"])
    fora = idade_num.notna() & ((idade_num < IDADE_MINIMA) | (idade_num > IDADE_MAXIMA))
    for idx in bruto.index[fora]:
        aud.registrar(bruto.at[idx, "id"], "idade",
                      f"idade_fora_de_{IDADE_MINIMA}_{IDADE_MAXIMA}",
                      bruto.at[idx, "idade"], None, idx)
        revisao.append({
            "linha_origem": idx, "id": bruto.at[idx, "id"], "pesid": bruto.at[idx, "pesid"],
            "coluna": "idade", "valor_original": bruto.at[idx, "idade"],
            "motivo": f"idade fora do intervalo plausivel {IDADE_MINIMA}-{IDADE_MAXIMA}",
            "acao": "valor convertido em ausencia; registro mantido na base",
        })
    bruto.loc[fora, "idade"] = pd.NA
    pd.DataFrame(revisao).to_csv(DIR_QUAR / "campos_para_revisao.csv", sep=";",
                                index=False, encoding="utf-8-sig")
    resumo["passos"]["6_campos_impossiveis"] = {
        "idade_fora_do_intervalo": int(fora.sum()),
        "intervalo_adotado": [IDADE_MINIMA, IDADE_MAXIMA],
        "arquivo": str(DIR_QUAR / "campos_para_revisao.csv"),
        "observacao": (
            "Regra deste projeto, nao do dicionario. O registro NAO foi excluido: "
            "apenas o valor impossivel virou ausencia, com o original na auditoria."
        ),
    }

    # ---------------- PASSO 7: integridade da chave ----------------
    print("[PASSO 7] Conferindo se as colunas de ocorrencia sao constantes por id...")
    grupos = bruto.groupby("id", dropna=False)
    conflito_por_coluna = {}
    ids_conflito: set = set()
    for coluna in COLS_OCORRENCIA:
        n_distintos = grupos[coluna].nunique(dropna=True)
        conflitantes = set(n_distintos[n_distintos > 1].index)
        conflito_por_coluna[coluna] = len(conflitantes)
        ids_conflito |= conflitantes
    resumo["passos"]["7_integridade_chave"] = {
        "ids_avaliados": int(bruto["id"].nunique()),
        "ids_com_conflito": len(ids_conflito),
        "conflitos_por_coluna": conflito_por_coluna,
    }
    print(f"          ids com conflito: {len(ids_conflito)}")

    linhas_quarentena = bruto[bruto["id"].isin(ids_conflito)].copy()
    if not linhas_quarentena.empty:
        linhas_quarentena.insert(0, "motivo_quarentena",
                                 "colunas de ocorrencia com valores divergentes dentro do mesmo id")
    linhas_quarentena.to_csv(DIR_QUAR / "registros_quarentena.csv", sep=";",
                             index=False, encoding="utf-8-sig")
    trabalho = bruto[~bruto["id"].isin(ids_conflito)].copy()

    # ---------------- PASSO 8: agregacao por ocorrencia ----------------
    print("[PASSO 8] Agregando para a unidade OCORRENCIA (sem somar linhas repetidas)...")
    # 8a. atributos da ocorrencia: primeiro valor (ja provado constante por id)
    ocor = trabalho.groupby("id", as_index=False)[COLS_OCORRENCIA].first()

    # 8b. contagens de pessoas: uma linha por (id, pesid) DISTINTO
    pessoas = (
        trabalho.dropna(subset=["pesid"])
        .drop_duplicates(subset=["id", "pesid"])[["id"] + COLS_PESSOA]
        .copy()
    )
    for c in ("ilesos", "feridos_leves", "feridos_graves", "mortos"):
        pessoas[c] = pd.to_numeric(pessoas[c], errors="coerce").astype("Int64")
    pessoas["idade"] = pd.to_numeric(pessoas["idade"], errors="coerce").astype("Int64")
    pessoas["sem_estado_fisico"] = (
        pessoas[["ilesos", "feridos_leves", "feridos_graves", "mortos"]].sum(axis=1) == 0
    ).astype(int)

    agg_pessoas = pessoas.groupby("id").agg(
        qtd_pessoas=("pesid", "nunique"),
        qtd_ilesos=("ilesos", "sum"),
        qtd_feridos_leves=("feridos_leves", "sum"),
        qtd_feridos_graves=("feridos_graves", "sum"),
        qtd_mortos=("mortos", "sum"),
        qtd_estado_fisico_nao_informado=("sem_estado_fisico", "sum"),
    ).reset_index()

    # 8c. veiculos: uma linha por (id, id_veiculo) DISTINTO
    agg_veiculos = (
        trabalho.dropna(subset=["id_veiculo"])
        .drop_duplicates(subset=["id", "id_veiculo"])
        .groupby("id").agg(qtd_veiculos=("id_veiculo", "nunique")).reset_index()
    )

    # 8d. causas e tipos: contexto apurado, fora do modelo principal
    agg_causas = trabalho.groupby("id").agg(
        qtd_causas_distintas=("causa_acidente", "nunique"),
        qtd_tipos_distintos=("tipo_acidente", "nunique"),
    ).reset_index()

    principal = (
        trabalho[trabalho["causa_principal"].map(chave_comparacao) == "sim"]
        .drop_duplicates(subset=["id"])[["id", "causa_acidente"]]
        .rename(columns={"causa_acidente": "causa_principal_acidente"})
    )
    tipo_um = (
        trabalho[trabalho["ordem_tipo_acidente"] == "1"]
        .drop_duplicates(subset=["id"])[["id", "tipo_acidente"]]
        .rename(columns={"tipo_acidente": "tipo_acidente_principal"})
    )

    for parte in (agg_pessoas, agg_veiculos, agg_causas, principal, tipo_um):
        ocor = ocor.merge(parte, on="id", how="left")

    for c in ("qtd_pessoas", "qtd_ilesos", "qtd_feridos_leves", "qtd_feridos_graves",
              "qtd_mortos", "qtd_estado_fisico_nao_informado", "qtd_veiculos",
              "qtd_causas_distintas", "qtd_tipos_distintos"):
        ocor[c] = pd.to_numeric(ocor[c], errors="coerce").fillna(0).astype("int64")
    ocor["qtd_feridos"] = ocor["qtd_feridos_leves"] + ocor["qtd_feridos_graves"]

    # ---------------- PASSO 9: atributos derivados ----------------
    print("[PASSO 9] Derivando atributos temporais...")
    data = pd.to_datetime(ocor["data_inversa"], format="%Y-%m-%d", errors="coerce")
    falhou_data = data.isna()
    ocor["data_inversa"] = data.dt.strftime("%Y-%m-%d").astype("string")
    ocor["ano"] = data.dt.year.astype("Int64")
    ocor["mes"] = data.dt.month.astype("Int64")
    ocor["mes_nome"] = ocor["mes"].map(MESES).astype("string")
    ocor["dia_semana_calculado"] = data.dt.dayofweek.map(DIA_SEMANA_POR_INDICE).astype("string")
    ocor["dia_semana_divergente"] = (
        ocor["dia_semana"].map(chave_comparacao) != ocor["dia_semana_calculado"].map(chave_comparacao)
    ).map({True: "Sim", False: "Não"}).astype("string")
    n_divergentes = int((ocor["dia_semana_divergente"] == "Sim").sum())
    for idx in ocor.index[ocor["dia_semana_divergente"] == "Sim"][:500]:
        aud.registrar(ocor.at[idx, "id"], "dia_semana", "divergencia_dia_semana_x_data",
                      ocor.at[idx, "dia_semana"], ocor.at[idx, "dia_semana_calculado"], idx)

    hora_txt = pd.to_datetime(ocor["horario"], format="%H:%M:%S", errors="coerce")
    falhou_hora = hora_txt.isna()
    ocor["horario"] = hora_txt.dt.strftime("%H:%M:%S").astype("string")
    ocor["hora"] = hora_txt.dt.hour.astype("Int64")
    ocor["faixa_horaria"] = ocor["hora"].map(
        lambda h: pd.NA if pd.isna(h) else faixa_da_hora(int(h))
    ).astype("string")
    ocor["fim_de_semana"] = ocor["dia_semana_calculado"].isin(["Sábado", "Domingo"]).map(
        {True: "Sim", False: "Não"}
    ).astype("string")

    ocor["br"] = para_numero(ocor["br"]).astype("Int64")
    ocor["km"] = formatar_decimal(para_numero(ocor["km"]), 1)
    ocor["latitude"] = formatar_decimal(para_numero(ocor["latitude"]), 8)
    ocor["longitude"] = formatar_decimal(para_numero(ocor["longitude"]), 8)

    resumo["passos"]["9_derivados"] = {
        "datas_que_falharam_na_conversao": int(falhou_data.sum()),
        "horarios_que_falharam_na_conversao": int(falhou_hora.sum()),
        "dia_semana_divergente": n_divergentes,
        "limites_faixa_horaria": contrato["colunas"]["faixa_horaria"]["limites"],
    }

    # ---------------- PASSO 10: elegibilidade ----------------
    print("[PASSO 10] Sinalizando alvo ausente e elegibilidade para o treino...")
    ocor["alvo_ausente"] = ocor["classificacao_acidente"].isna().map(
        {True: "Sim", False: "Não"}
    ).astype("string")
    # Somente alvo ausente bloqueia o treino. Ausencia em ENTRADA nao bloqueia:
    # ela e tratada por imputacao dentro do Pipeline, ajustado apenas no treino.
    ocor["elegivel_modelo"] = ocor["alvo_ausente"].map({"Sim": "Não", "Não": "Sim"}).astype("string")
    ocor["motivo_inelegibilidade"] = ocor["alvo_ausente"].map(
        {"Sim": "classificacao_acidente ausente", "Não": pd.NA}
    ).astype("string")

    # Coluna separada, informativa: quais entradas do modelo faltam nesta linha.
    # Fica fora de motivo_inelegibilidade justamente para nao dar a impressao de
    # que ausencia em entrada torna o registro inelegivel.
    colunas_entrada = [c for c in contrato["entradas_modelo_permitidas"] if c in ocor.columns]
    faltantes = ocor[colunas_entrada].isna()
    ocor["entradas_ausentes"] = faltantes.apply(
        lambda linha: "; ".join(c for c in colunas_entrada if linha[c]) or pd.NA, axis=1
    ).astype("string")

    resumo["passos"]["10_elegibilidade"] = {
        "ocorrencias": int(len(ocor)),
        "alvo_ausente": int((ocor["alvo_ausente"] == "Sim").sum()),
        "elegiveis_para_treino": int((ocor["elegivel_modelo"] == "Sim").sum()),
        "inelegiveis": int((ocor["elegivel_modelo"] == "Não").sum()),
        "com_alguma_entrada_ausente": int(ocor["entradas_ausentes"].notna().sum()),
        "regra": "Somente alvo ausente torna a ocorrencia inelegivel. Ausencia em entrada e imputada dentro do Pipeline, ajustado apenas no treino.",
    }

    # ---------------- PASSO 11: exportacao ----------------
    print("[PASSO 11] Exportando base limpa, esquema, auditoria e relatorios...")
    faltando = [c for c in ORDEM_COLUNAS_OCORRENCIA if c not in ocor.columns]
    if faltando:
        print(f"[ERRO] Colunas esperadas ausentes: {faltando}")
        return 1
    ocor = ocor[ORDEM_COLUNAS_OCORRENCIA].sort_values("id", key=lambda s: s.astype("int64"))
    ocor = ocor.reset_index(drop=True)

    saida = DIR_PROC / "prf_limpo.csv"
    ocor.to_csv(saida, **ESCRITA_LIMPO)

    pessoas_saida = pessoas.copy()
    pessoas_saida = pessoas_saida.sort_values(
        ["id", "pesid"], key=lambda s: pd.to_numeric(s, errors="coerce")
    ).reset_index(drop=True)
    pessoas_saida.to_csv(DIR_PROC / "prf_pessoas.csv", **ESCRITA_LIMPO)

    # Esquema de leitura: o CSV nao guarda tipos, entao gravamos como reabrir.
    esquema = {
        "arquivo": saida.name,
        "versao_contrato": contrato["versao_contrato"],
        "leitura": {"sep": ";", "encoding": "utf-8-sig", "decimal": ",", "dtype": "str"},
        "observacao": (
            "Leia sempre com dtype=str para preservar o texto original e converta "
            "depois, conforme o tipo declarado abaixo."
        ),
        "colunas": {
            c: {
                "tipo": contrato["colunas"].get(c, {}).get("tipo", "texto"),
                "papel": contrato["colunas"].get(c, {}).get("papel", "nao_declarado"),
                "nulo_permitido": contrato["colunas"].get(c, {}).get("nulo_permitido", True),
            }
            for c in ORDEM_COLUNAS_OCORRENCIA
        },
    }
    salvar_json(esquema, DIR_PROC / "prf_limpo_esquema.json")

    info_aud = aud.salvar(DIR_REPORTS / "auditoria_limpeza.csv")
    info_aud["observacao"] = (
        "Para as regras que atingem centenas de milhares de celulas (mapeamento de "
        "dia_semana, uso_solo, tokens de ausencia, reordenacao de tracado_via), a "
        "auditoria grava uma AMOSTRA rastreavel por regra, com limite fixo no codigo. "
        "As contagens completas de cada regra estao em passos.3_texto, "
        "passos.4_tokens_ausencia e passos.5_categorias deste mesmo relatorio."
    )
    resumo["auditoria"] = info_aud

    # ---- reconciliacao: destinos mutuamente exclusivos das linhas de entrada ----
    recon = pd.DataFrame([
        {"destino": "linhas de entrada", "linhas": n_entrada},
        {"destino": "duplicatas exatas removidas", "linhas": int(antes["duplicatas_exatas"])},
        {"destino": "linhas enviadas a quarentena", "linhas": int(len(linhas_quarentena))},
        {"destino": "linhas mantidas e agregadas", "linhas": int(len(trabalho))},
    ])
    recon.to_csv(DIR_REPORTS / "reconciliacao.csv", sep=";", index=False, encoding="utf-8-sig")
    soma_destinos = int(antes["duplicatas_exatas"]) + len(linhas_quarentena) + len(trabalho)
    resumo["reconciliacao"] = {
        "linhas_entrada": n_entrada,
        "duplicatas_exatas_removidas": int(antes["duplicatas_exatas"]),
        "linhas_quarentena": int(len(linhas_quarentena)),
        "linhas_mantidas_agregadas": int(len(trabalho)),
        "soma_dos_destinos": soma_destinos,
        "reconciliado": soma_destinos == n_entrada,
        "ocorrencias_resultantes": int(len(ocor)),
        "pessoas_distintas_resultantes": int(len(pessoas_saida)),
    }

    # ---- qualidade antes x depois ----
    depois = {
        "linhas": int(len(ocor)),
        "colunas": int(ocor.shape[1]),
        "nulos_por_coluna": {c: int(ocor[c].isna().sum()) for c in ocor.columns},
        "duplicatas_exatas": int(ocor.duplicated().sum()),
        "ids_distintos": int(ocor["id"].nunique()),
        "valores_distintos_tracado_via": int(ocor["tracado_via"].nunique()),
        "categorias_dia_semana": sorted(ocor["dia_semana"].dropna().unique().tolist()),
        "categorias_uso_solo": sorted(ocor["uso_solo"].dropna().unique().tolist()),
    }
    linhas_qad = [
        {"metrica": "unidade do registro", "antes": "pessoa x causa x tipo",
         "depois": "ocorrencia de acidente"},
        {"metrica": "linhas", "antes": antes["linhas"], "depois": depois["linhas"]},
        {"metrica": "colunas", "antes": antes["colunas"], "depois": depois["colunas"]},
        {"metrica": "ids distintos", "antes": antes["ids_distintos"], "depois": depois["ids_distintos"]},
        {"metrica": "duplicatas exatas", "antes": antes["duplicatas_exatas"],
         "depois": depois["duplicatas_exatas"]},
        {"metrica": "rotulos distintos em tracado_via",
         "antes": antes["valores_distintos_tracado_via"],
         "depois": depois["valores_distintos_tracado_via"]},
        {"metrica": "categorias de dia_semana",
         "antes": ", ".join(antes["categorias_dia_semana"]),
         "depois": ", ".join(depois["categorias_dia_semana"])},
        {"metrica": "categorias de uso_solo",
         "antes": ", ".join(antes["categorias_uso_solo"]),
         "depois": ", ".join(depois["categorias_uso_solo"])},
        {"metrica": "celulas de texto corrigidas", "antes": "-", "depois": alteracoes_texto},
        {"metrica": "registros na auditoria", "antes": "-",
         "depois": info_aud["registros_auditoria"]},
    ]
    for coluna in ("classificacao_acidente", "condicao_metereologica", "sentido_via",
                   "fase_dia", "tipo_pista", "tracado_via", "uso_solo", "km", "br"):
        linhas_qad.append({
            "metrica": f"nulos em {coluna}",
            "antes": antes["nulos_por_coluna"].get(coluna, "-"),
            "depois": depois["nulos_por_coluna"].get(coluna, "-"),
        })
    df_qad = pd.DataFrame(linhas_qad)
    # Nome proprio da limpeza. O arquivo qualidade_antes_depois.csv e gerado pelo
    # validador, que mede o "depois" de forma independente, reabrindo o CSV salvo.
    df_qad.to_csv(DIR_REPORTS / "limpeza_antes_depois.csv", sep=";",
                  index=False, encoding="utf-8-sig")

    # ---- composicao das classes: exclusoes mudaram o equilibrio? ----
    todas = ocor["classificacao_acidente"].value_counts(dropna=False)
    elegiveis = ocor.loc[ocor["elegivel_modelo"] == "Sim", "classificacao_acidente"].value_counts()
    comp = pd.DataFrame({"base_limpa": todas, "elegiveis_para_treino": elegiveis}).fillna(0).astype(int)
    comp["pct_base_limpa"] = (100 * comp["base_limpa"] / comp["base_limpa"].sum()).round(3)
    comp["pct_elegiveis"] = (100 * comp["elegiveis_para_treino"] / comp["elegiveis_para_treino"].sum()).round(3)
    comp.index.name = "classificacao_acidente"
    comp.to_csv(DIR_REPORTS / "composicao_classes.csv", sep=";", encoding="utf-8-sig")
    resumo["composicao_classes"] = comp.reset_index().to_dict(orient="records")

    resumo["saidas"] = {
        "base_limpa_ocorrencia": str(saida),
        "sha256_base_limpa": hash_arquivo(saida),
        "base_pessoas": str(DIR_PROC / "prf_pessoas.csv"),
        "esquema": str(DIR_PROC / "prf_limpo_esquema.json"),
        "auditoria": str(DIR_REPORTS / "auditoria_limpeza.csv"),
        "quarentena_registros": str(DIR_QUAR / "registros_quarentena.csv"),
        "quarentena_campos": str(DIR_QUAR / "campos_para_revisao.csv"),
        "limpeza_antes_depois": str(DIR_REPORTS / "limpeza_antes_depois.csv"),
        "reconciliacao": str(DIR_REPORTS / "reconciliacao.csv"),
        "mapa_tracado_via": str(DIR_REPORTS / "mapa_tracado_via.csv"),
        "composicao_classes": str(DIR_REPORTS / "composicao_classes.csv"),
    }
    salvar_json(resumo, DIR_REPORTS / "limpeza.json")
    escrever_markdown_limpeza(resumo, df_qad, comp, DIR_REPORTS / "limpeza.md")

    print()
    print("=" * 72)
    print(f"Entrada:  {n_entrada} linhas (pessoa x causa x tipo)")
    print(f"Saida:    {len(ocor)} ocorrencias em {saida}")
    print(f"Pessoas:  {len(pessoas_saida)} registros em prf_pessoas.csv")
    print(f"Quarentena: {len(linhas_quarentena)} linhas | Campos revisados: {len(revisao)}")
    print(f"Reconciliado: {resumo['reconciliacao']['reconciliado']}")
    print(f"Alvo ausente: {resumo['passos']['10_elegibilidade']['alvo_ausente']} ocorrencia(s)")
    print("=" * 72)
    return 0


def escrever_markdown_limpeza(resumo, df_qad, comp, caminho: Path) -> None:
    L = ["# Limpeza e transformacao - antes x depois\n"]
    L.append(f"- Entrada: `{resumo['entrada']['caminho']}`")
    L.append(f"- SHA-256 da entrada: `{resumo['entrada']['sha256']}`")
    L.append(f"- Saida: `{resumo['saidas']['base_limpa_ocorrencia']}`")
    L.append(f"- SHA-256 da saida: `{resumo['saidas']['sha256_base_limpa']}`")
    L.append(f"- Contrato: versao {resumo['versao_contrato']}")
    L.append(f"- Execucao: {resumo['ambiente']['executado_em']}\n")
    L.append("## Reconciliacao das linhas de entrada\n")
    r = resumo["reconciliacao"]
    L.append(f"- Linhas de entrada: {r['linhas_entrada']}")
    L.append(f"- Duplicatas exatas removidas: {r['duplicatas_exatas_removidas']}")
    L.append(f"- Linhas em quarentena: {r['linhas_quarentena']}")
    L.append(f"- Linhas mantidas e agregadas: {r['linhas_mantidas_agregadas']}")
    L.append(f"- Soma dos destinos igual a entrada: **{r['reconciliado']}**")
    L.append(f"- Ocorrencias resultantes: {r['ocorrencias_resultantes']}")
    L.append(f"- Pessoas distintas resultantes: {r['pessoas_distintas_resultantes']}\n")
    L.append("## Tabela antes x depois\n")
    L.append(tabela_markdown(df_qad))
    L.append("\n## Composicao das classes\n")
    L.append(tabela_markdown(comp.reset_index()))
    L.append("\n## Passos executados\n")
    for nome, dados in resumo["passos"].items():
        L.append(f"### {nome}\n")
        L.append("```json")
        import json as _json
        L.append(_json.dumps(dados, ensure_ascii=False, indent=2, default=str))
        L.append("```\n")
    caminho.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
