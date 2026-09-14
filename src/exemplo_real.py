r"""
exemplo_real.py - ETAPA 5b: recortes ANTES x DEPOIS com dados REAIS da PRF.

Complementa src/exemplo_ficticio.py. La os registros F01-F05 sao inventados e
servem para explicar as regras; aqui as linhas sao reais e rastreaveis pelo `id`
da ocorrencia, o que permite abrir o arquivo bruto e a base limpa e conferir
celula por celula durante a apresentacao.

Sao gerados dois recortes, porque os dois problemas centrais do projeto sao
diferentes e nao caberiam na mesma tabela:

  1) AGREGACAO - por que o numero de linhas cai de 584.010 para 72.529.
     O arquivo bruto repete a ocorrencia uma vez por (pessoa x causa x tipo).
     A ocorrencia escolhida mostra o efeito pratico: somar a coluna `mortos`
     das linhas brutas conta a mesma vitima mais de uma vez.

  2) PADRONIZACAO - o que muda dentro de cada celula.
     Cinco ocorrencias reais, cada uma escolhida por exibir um problema
     diferente (token "Ignorado", `tracado_via` fora de ordem, `uso_solo` como
     "Sim"/"Nao", `dia_semana` em minusculas, `sentido_via` nao informado).

A selecao e deterministica: dados os mesmos arquivos de entrada, as mesmas
ocorrencias sao escolhidas. Nada e sorteado.

Saidas em reports/:
  exemplo_real_agregacao_antes.csv|.png    linhas brutas de uma ocorrencia
  exemplo_real_agregacao_depois.csv|.png   a linha unica correspondente na base limpa
  exemplo_real_antes.csv|.png              cinco ocorrencias, valores brutos
  exemplo_real_depois.csv|.png             as mesmas cinco, ja padronizadas
  exemplo_real_mudancas.csv|.png           so as celulas que realmente mudaram
  exemplo_real_derivados.csv|.png          atributos criados na transformacao
  exemplo_real.md                          leitura guiada dos recortes

Uso:
  python src\exemplo_real.py
  python src\exemplo_real.py --ids 652588 652492 652653
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from comum import (
    DIR_PROC,
    DIR_RAW,
    ESCRITA_LIMPO,
    LEITURA_BRUTO,
    NOME_CSV_BRUTO,
    TOKENS_AUSENCIA,
    DIR_REPORTS,
    encurtar,
    garantir_pastas,
    salvar_tabela_imagem,
    tabela_markdown,
)

# Colunas lidas do arquivo bruto. Ler as 37 colunas de 584 mil linhas nao e
# necessario e deixaria o script lento sem ganho nenhum.
COLUNAS_BRUTO = [
    "id", "pesid", "data_inversa", "dia_semana", "horario", "uf", "br", "km",
    "municipio", "causa_acidente", "ordem_tipo_acidente", "tipo_acidente",
    "classificacao_acidente", "fase_dia", "sentido_via", "condicao_metereologica",
    "tipo_pista", "tracado_via", "uso_solo", "tipo_envolvido", "estado_fisico",
    "ilesos", "feridos_leves", "feridos_graves", "mortos",
]

# Recorte da ocorrencia usado na imagem de agregacao. Mostra o que VARIA de
# linha para linha; as colunas da ocorrencia (data, UF, clima...) sao identicas
# nas seis linhas e por isso ficam de fora, com aviso na nota da figura.
VITRINE_AGREGACAO_ANTES = [
    "pesid", "tipo_envolvido", "causa_acidente", "ordem_tipo_acidente",
    "tipo_acidente", "estado_fisico", "ilesos", "feridos_leves", "mortos",
]

VITRINE_AGREGACAO_DEPOIS = [
    "id", "qtd_pessoas", "qtd_ilesos", "qtd_feridos_leves", "qtd_feridos_graves",
    "qtd_mortos", "qtd_causas_distintas", "qtd_tipos_distintos",
    "classificacao_acidente",
]

# Colunas comparaveis entre bruto e limpo: existem com o mesmo nome nos dois
# lados, o que permite montar a tabela de mudancas celula por celula.
COLUNAS_COMPARAVEIS = [
    "data_inversa", "dia_semana", "horario", "uf", "fase_dia", "sentido_via",
    "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
    "classificacao_acidente",
]

# Atributos que nao existiam no bruto: sao derivados na limpeza.
DERIVADOS = ["mes_nome", "faixa_horaria", "fim_de_semana", "elegivel_modelo"]

# Nome da regra que produziu cada mudanca. Sao os MESMOS rotulos gravados por
# src/limpeza.py no registro de auditoria (reports/auditoria_limpeza.csv), para a
# figura do slide e o arquivo de auditoria contarem a mesma historia.
REGRA_POR_COLUNA = {
    "dia_semana": "mapa_dia_semana",
    "uso_solo": "mapa_uso_solo_dicionario",
    "fase_dia": "mapa_fase_dia",
    "tipo_pista": "mapa_tipo_pista",
    "condicao_metereologica": "mapa_condicao_metereologica",
    "sentido_via": "mapa_sentido_via",
    "tracado_via": "ordenacao_componentes",
    "uf": "uf_em_maiusculas",
}


def carregar_bruto(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(
        caminho,
        usecols=COLUNAS_BRUTO,
        dtype=str,
        na_values=TOKENS_AUSENCIA,
        keep_default_na=False,
        **LEITURA_BRUTO,
    )


def escolher_ocorrencia_agregacao(bruto: pd.DataFrame) -> str:
    """Escolhe a ocorrencia que melhor demonstra a contagem duplicada de vitimas.

    Critério: entre as ocorrencias pequenas o suficiente para caber num slide
    (4 a 8 linhas brutas), pega a que tem a MAIOR diferenca entre somar a coluna
    `mortos` linha a linha e contar mortos por pessoa distinta. Empate e
    resolvido pelo menor `id`, para a escolha nao depender da ordem do arquivo.
    """
    linhas = bruto.groupby("id").size()
    candidatas = linhas[(linhas >= 4) & (linhas <= 8)].index
    sub = bruto[bruto["id"].isin(candidatas)]

    morto = sub["mortos"].fillna("0").str.strip().eq("1")
    ingenuo = morto.groupby(sub["id"]).sum()
    real = (
        sub.assign(_m=morto)
        .drop_duplicates(["id", "pesid"])
        .groupby("id")["_m"]
        .sum()
    )
    ganho = (ingenuo - real).sort_index()
    if ganho.max() <= 0:  # base sem duplicacao: cai para a ocorrencia com mais linhas
        return str(linhas[candidatas].idxmax())
    return str(ganho.idxmax())


def escolher_ocorrencias_padronizacao(bruto: pd.DataFrame, quantidade: int) -> list[str]:
    """Pega uma ocorrencia real para cada problema de padronizacao conhecido.

    Cada criterio devolve uma ocorrencia de uma posicao FIXA da sua lista de
    candidatas ordenada: o criterio k pega a candidata na fracao (k+1)/(n+1) da
    lista. Isso mantem a selecao reproduzivel e, como o `id` cresce junto com a
    data, espalha os exemplos pelo ano em vez de cair tudo em janeiro.

    Se algum criterio nao encontrar nada (base diferente), ele e ignorado em vez
    de derrubar o script.
    """
    ocorrencias = bruto.drop_duplicates("id").set_index("id")

    def fora_de_ordem(valor) -> bool:
        if pd.isna(valor):
            return False
        partes = [p.strip() for p in str(valor).split(";")]
        return len(partes) > 1 and partes != sorted(set(partes))

    criterios = [
        ("tracado_via multivalorado fora de ordem",
         ocorrencias["tracado_via"].map(fora_de_ordem)),
        ("condicao_metereologica = \"Ignorado\"",
         ocorrencias["condicao_metereologica"].eq("Ignorado")),
        ("sentido_via = \"Nao Informado\"",
         ocorrencias["sentido_via"].fillna("").str.strip().str.casefold()
         .isin(["não informado", "nao informado"])),
        ("uso_solo = \"Sim\" (area urbana)", ocorrencias["uso_solo"].eq("Sim")),
        ("fim de semana com vitima fatal",
         ocorrencias["dia_semana"].isin(["sábado", "domingo"])
         & ocorrencias["classificacao_acidente"].eq("Com Vítimas Fatais")),
    ]

    escolhidos: list[str] = []
    for k, (_, mascara) in enumerate(criterios):
        if len(escolhidos) >= quantidade:
            break
        # Ordena por valor numerico: `id` e texto, e ordem alfabetica colocaria
        # "1000000" antes de "999999".
        elegiveis = sorted(
            (i for i in ocorrencias.index[mascara] if i not in escolhidos),
            key=lambda s: (len(s), s),
        )
        if not elegiveis:
            continue
        posicao = min(len(elegiveis) - 1, len(elegiveis) * (k + 1) // (len(criterios) + 1))
        escolhidos.append(elegiveis[posicao])
    return escolhidos


def montar_mudancas(bruto_ocorrencia: pd.DataFrame, limpo: pd.DataFrame) -> pd.DataFrame:
    """Tabela longa 'id | coluna | antes | depois' apenas com o que mudou.

    Formato longo de proposito: no slide, uma lista curta de mudancas reais e
    mais facil de acompanhar do que duas tabelas largas lado a lado. Os atributos
    derivados ficam de fora e vao para a tabela propria, senao a mesma informacao
    ("nao existia") se repetiria em toda ocorrencia e a figura nao caberia.
    """
    registros = []
    for id_oc in bruto_ocorrencia["id"]:
        antes = bruto_ocorrencia.set_index("id").loc[id_oc]
        depois = limpo.set_index("id").loc[id_oc]
        for coluna in COLUNAS_COMPARAVEIS:
            v_antes, v_depois = antes[coluna], depois[coluna]
            iguais = (pd.isna(v_antes) and pd.isna(v_depois)) or (
                not pd.isna(v_antes) and not pd.isna(v_depois)
                and str(v_antes) == str(v_depois)
            )
            if iguais:
                continue
            registros.append({
                "id": id_oc,
                "coluna": coluna,
                "antes (arquivo bruto)": encurtar(v_antes, 26),
                "depois (base limpa)": encurtar(v_depois, 26),
                "regra aplicada": (
                    # Virar vazio nao e mapeamento: e o token de ausencia disfarcado
                    # de categoria ("Ignorado", "Nao Informado") sendo reconhecido.
                    "token_ausencia" if pd.isna(v_depois)
                    else REGRA_POR_COLUNA.get(coluna, "limpeza_texto")
                ),
            })
    return pd.DataFrame(registros)


def montar_derivados(limpo_ocorrencia: pd.DataFrame) -> pd.DataFrame:
    """Atributos que nao existiam no arquivo bruto, calculados na transformacao."""
    df = limpo_ocorrencia.set_index("id")[DERIVADOS].reset_index()
    df.columns = ["id"] + [f"{c} (novo)" for c in DERIVADOS]
    return df


def gerar_agregacao(bruto: pd.DataFrame, limpo: pd.DataFrame, id_oc: str) -> dict:
    """Figuras e CSVs do recorte de agregacao (N linhas brutas -> 1 linha limpa)."""
    linhas = bruto[bruto["id"] == id_oc].copy()
    linha_limpa = limpo[limpo["id"] == id_oc]

    morto = linhas["mortos"].fillna("0").str.strip().eq("1")
    resumo = {
        "id": id_oc,
        "linhas_brutas": int(len(linhas)),
        "pessoas_distintas": int(linhas["pesid"].nunique(dropna=False)),
        "causas_distintas": int(linhas["causa_acidente"].nunique()),
        "tipos_distintos": int(linhas["tipo_acidente"].nunique()),
        "mortos_somando_linhas": int(morto.sum()),
        "mortos_por_pessoa_distinta": int(
            linhas.assign(_m=morto).drop_duplicates(["id", "pesid"])["_m"].sum()
        ),
    }

    vitrine = linhas[VITRINE_AGREGACAO_ANTES].copy()
    vitrine["causa_acidente"] = vitrine["causa_acidente"].map(lambda v: encurtar(v, 24))
    vitrine["tipo_acidente"] = vitrine["tipo_acidente"].map(lambda v: encurtar(v, 22))
    vitrine.insert(0, "linha", range(1, len(vitrine) + 1))

    linhas.to_csv(DIR_REPORTS / "exemplo_real_agregacao_antes.csv", **ESCRITA_LIMPO)
    linha_limpa.to_csv(DIR_REPORTS / "exemplo_real_agregacao_depois.csv", **ESCRITA_LIMPO)

    # Destaca a coluna `mortos`: e a evidencia visual da contagem duplicada.
    col_mortos = list(vitrine.columns).index("mortos")
    salvar_tabela_imagem(
        vitrine,
        f"ANTES — ocorrencia id={id_oc} ocupa {resumo['linhas_brutas']} linhas no arquivo bruto",
        DIR_REPORTS / "exemplo_real_agregacao_antes.png",
        nota=(
            "Dados reais da PRF (2025). As colunas da ocorrencia (data, UF, BR, km, clima, "
            "pista, tracado) repetem valor identico nas "
            f"{resumo['linhas_brutas']} linhas e foram omitidas aqui. Somar a coluna 'mortos' "
            f"linha a linha da {resumo['mortos_somando_linhas']}; ha "
            f"{resumo['mortos_por_pessoa_distinta']} vitima(s) fatal(is) de verdade."
        ),
        destacar={(i, col_mortos) for i in range(len(vitrine))},
    )

    vitrine_depois = linha_limpa[VITRINE_AGREGACAO_DEPOIS].copy()
    salvar_tabela_imagem(
        vitrine_depois,
        f"DEPOIS — a mesma ocorrencia id={id_oc} vira 1 linha, com as vitimas contadas por pessoa",
        DIR_REPORTS / "exemplo_real_agregacao_depois.png",
        nota=(
            "Dados reais da PRF (2025). Contagens feitas sobre pares (id, pesid) distintos, "
            "nao sobre as linhas brutas."
        ),
        largura_col=1.9,
    )
    return resumo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Recortes ANTES x DEPOIS com dados reais.")
    p.add_argument("--entrada", default=str(DIR_RAW / NOME_CSV_BRUTO),
                   help="CSV bruto da PRF.")
    p.add_argument("--limpo", default=str(DIR_PROC / "prf_limpo.csv"),
                   help="CSV limpo gerado por src/limpeza.py.")
    p.add_argument("--ids", nargs="*", default=None,
                   help="Ocorrencias para o recorte de padronizacao (opcional).")
    p.add_argument("--quantidade", type=int, default=5,
                   help="Quantas ocorrencias no recorte de padronizacao.")
    args = p.parse_args(argv)

    garantir_pastas()
    caminho_bruto, caminho_limpo = Path(args.entrada), Path(args.limpo)
    for caminho in (caminho_bruto, caminho_limpo):
        if not caminho.exists():
            print(f"ERRO: arquivo nao encontrado: {caminho}")
            return 2

    print(f"Lendo bruto: {caminho_bruto.name}")
    bruto = carregar_bruto(caminho_bruto)
    print(f"  {len(bruto):,} linhas | {bruto['id'].nunique():,} ocorrencias distintas")

    limpo = pd.read_csv(caminho_limpo, sep=";", encoding="utf-8-sig", dtype=str,
                        keep_default_na=True)
    print(f"Lendo limpo: {caminho_limpo.name}")
    print(f"  {len(limpo):,} linhas")

    # ---- recorte 1: agregacao ----
    id_agregacao = escolher_ocorrencia_agregacao(bruto)
    resumo = gerar_agregacao(bruto, limpo, id_agregacao)
    print(f"\nAgregacao: id={id_agregacao} "
          f"({resumo['linhas_brutas']} linhas -> 1, "
          f"mortos {resumo['mortos_somando_linhas']} -> {resumo['mortos_por_pessoa_distinta']})")

    # ---- recorte 2: padronizacao ----
    ids = args.ids or escolher_ocorrencias_padronizacao(bruto, args.quantidade)
    ids = [i for i in ids if i in set(limpo["id"])]
    if not ids:
        print("ERRO: nenhuma ocorrencia valida para o recorte de padronizacao.")
        return 3
    print(f"Padronizacao: ids={', '.join(ids)}")

    antes = (
        bruto[bruto["id"].isin(ids)]
        .drop_duplicates("id")
        .set_index("id")
        .loc[ids]
        .reset_index()
    )
    depois = limpo[limpo["id"].isin(ids)].set_index("id").loc[ids].reset_index()

    vitrine_antes = antes[[
        "id", "data_inversa", "dia_semana", "horario", "uf", "fase_dia",
        "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
        "sentido_via", "classificacao_acidente",
    ]].map(lambda v: encurtar(v, 22))
    vitrine_depois = depois[[
        "id", "data_inversa", "dia_semana", "faixa_horaria", "fim_de_semana",
        "mes_nome", "uf", "fase_dia", "condicao_metereologica", "tipo_pista",
        "tracado_via", "uso_solo", "sentido_via", "classificacao_acidente",
        "elegivel_modelo",
    ]].map(lambda v: encurtar(v, 22))

    vitrine_antes.to_csv(DIR_REPORTS / "exemplo_real_antes.csv", **ESCRITA_LIMPO)
    vitrine_depois.to_csv(DIR_REPORTS / "exemplo_real_depois.csv", **ESCRITA_LIMPO)

    nota_real = ("Dados reais da PRF (2025). Os `id` sao os do arquivo original: "
                 "da para conferir linha por linha na base bruta e na base limpa.")
    salvar_tabela_imagem(
        vitrine_antes,
        "ANTES — cinco ocorrencias reais como aparecem no arquivo bruto",
        DIR_REPORTS / "exemplo_real_antes.png",
        nota=nota_real, largura_col=1.5,
    )
    salvar_tabela_imagem(
        vitrine_depois,
        "DEPOIS — as mesmas cinco ocorrencias na base limpa (prf_limpo.csv)",
        DIR_REPORTS / "exemplo_real_depois.png",
        nota=nota_real + " As colunas faixa_horaria, fim_de_semana, mes_nome e "
        "elegivel_modelo nao existiam no arquivo bruto: sao derivadas na transformacao.",
        largura_col=1.5,
    )

    mudancas = montar_mudancas(antes, depois)
    mudancas.to_csv(DIR_REPORTS / "exemplo_real_mudancas.csv", **ESCRITA_LIMPO)
    salvar_tabela_imagem(
        mudancas,
        "Celula por celula: o que mudou nessas cinco ocorrencias reais",
        DIR_REPORTS / "exemplo_real_mudancas.png",
        nota=nota_real + " Celulas cujo valor bruto ja estava correto foram omitidas. "
        "A coluna 'regra aplicada' usa os mesmos nomes do registro de auditoria.",
        largura_col=2.2,
    )

    derivados = montar_derivados(depois)
    derivados.to_csv(DIR_REPORTS / "exemplo_real_derivados.csv", **ESCRITA_LIMPO)
    salvar_tabela_imagem(
        derivados,
        "Atributos derivados: nao existiam no arquivo bruto",
        DIR_REPORTS / "exemplo_real_derivados.png",
        nota="Dados reais da PRF (2025). Calculados a partir de data_inversa, horario e "
        "classificacao_acidente. Nenhum valor foi inventado ou imputado.",
        largura_col=1.9,
    )

    # ---- relatorio ----
    L = [
        "# Recortes ANTES x DEPOIS com dados REAIS\n",
        "> Ao contrario de `reports/exemplo_ficticio.md`, **todas as linhas desta pagina "
        "sao reais** e rastreaveis pelo `id` da ocorrencia no arquivo bruto da PRF.\n",
        "## 1. Agregacao: de varias linhas para uma ocorrencia\n",
        f"A ocorrencia **id={resumo['id']}** ocupa **{resumo['linhas_brutas']} linhas** no "
        f"arquivo bruto, porque o arquivo repete a ocorrencia uma vez para cada combinacao "
        f"de (pessoa x causa x tipo de acidente): sao "
        f"{resumo['pessoas_distintas']} pessoa(s), {resumo['causas_distintas']} causa(s) e "
        f"{resumo['tipos_distintos']} tipo(s).\n",
        f"Consequencia pratica: somar a coluna `mortos` linha a linha resulta em "
        f"**{resumo['mortos_somando_linhas']} mortos**, mas a ocorrencia teve "
        f"**{resumo['mortos_por_pessoa_distinta']}** vitima fatal. A contagem correta exige "
        "contar pares `(id, pesid)` distintos, e e isso que `src/limpeza.py` faz.\n",
        "### ANTES (linhas brutas)\n", tabela_markdown(
            bruto[bruto["id"] == resumo["id"]][VITRINE_AGREGACAO_ANTES]
        ),
        "\n### DEPOIS (linha unica na base limpa)\n", tabela_markdown(
            limpo[limpo["id"] == resumo["id"]][VITRINE_AGREGACAO_DEPOIS]
        ),
        "\nFiguras: `exemplo_real_agregacao_antes.png` e "
        "`exemplo_real_agregacao_depois.png`.\n",
        "## 2. Padronizacao: o que muda dentro da celula\n",
        f"Ocorrencias usadas: {', '.join('`' + i + '`' for i in ids)}. Cada uma foi "
        "escolhida por exibir um problema diferente encontrado no diagnostico.\n",
        "### ANTES\n", tabela_markdown(vitrine_antes),
        "\n### DEPOIS\n", tabela_markdown(vitrine_depois),
        "\n### Somente as celulas que mudaram\n", tabela_markdown(mudancas),
        "\n### Atributos derivados (nao existiam no bruto)\n", tabela_markdown(derivados),
        "\nFiguras: `exemplo_real_antes.png`, `exemplo_real_depois.png`, "
        "`exemplo_real_mudancas.png` e `exemplo_real_derivados.png`.\n",
        "## Como conferir na apresentacao\n",
        "1. Abrir `data/raw/acidentes2025_todas_causas_tipos.csv` e filtrar pelo `id`.",
        "2. Abrir `data/processed/prf_limpo.csv` e filtrar pelo mesmo `id`.",
        "3. Comparar com a tabela de mudancas acima: cada celula alterada tem regra "
        "correspondente em `config/regras_qualidade.json` e aparece no registro de "
        "auditoria `reports/auditoria_limpeza.csv`.\n",
    ]
    (DIR_REPORTS / "exemplo_real.md").write_text("\n".join(L), encoding="utf-8")

    print("\nArquivos gerados em reports/:")
    for nome in ("exemplo_real_agregacao_antes.csv", "exemplo_real_agregacao_antes.png",
                 "exemplo_real_agregacao_depois.csv", "exemplo_real_agregacao_depois.png",
                 "exemplo_real_antes.csv", "exemplo_real_antes.png",
                 "exemplo_real_depois.csv", "exemplo_real_depois.png",
                 "exemplo_real_mudancas.csv", "exemplo_real_mudancas.png",
                 "exemplo_real_derivados.csv", "exemplo_real_derivados.png",
                 "exemplo_real.md"):
        print(f"  - {nome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
