r"""
exemplo_ficticio.py - ETAPA 5: tabela ANTES x DEPOIS para o slide.

ATENCAO PEDAGOGICA: os cinco registros F01-F05 sao INVENTADOS. Eles imitam o
esquema real confirmado no dicionario da PRF, mas nao sao dados reais e NAO entram
em nenhum grafico, treinamento ou metrica deste projeto. Servem apenas para mostrar
visualmente o efeito da padronizacao e dos atributos derivados.

Cada registro foi montado para exibir um problema diferente, todos observados de
verdade no arquivo bruto:
  F01 - dia_semana em minusculas, uso_solo como "Sim", fase_dia com "Pleno dia"
  F02 - tracado_via multivalorado fora de ordem ("Reta;Declive")
  F03 - condicao_metereologica com o token "Ignorado" (ausencia disfarcada)
  F04 - sentido_via "Nao Informado" e espacos sobrando no texto
  F05 - classificacao_acidente vazia: alvo ausente, registro fica inelegivel

Saidas:
  reports/exemplo_antes.csv
  reports/exemplo_depois.csv
  reports/exemplo_antes_depois.png       (imagem legivel para slide)
  reports/exemplo_codificacao.csv        (recorte do one-hot)
  reports/exemplo_codificacao.png
  reports/exemplo_ficticio.md

Uso:
  python src\exemplo_ficticio.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # sem janela grafica: salva direto em arquivo
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from comum import DIR_REPORTS, garantir_pastas, tabela_markdown  # noqa: E402
from limpeza import (  # noqa: E402
    DIA_SEMANA_POR_INDICE,
    MAPA_CONDICAO,
    MAPA_DIA_SEMANA,
    MAPA_FASE_DIA,
    MAPA_SENTIDO,
    MAPA_TIPO_PISTA,
    MAPA_USO_SOLO,
    MESES,
    canonizar_tracado,
    faixa_da_hora,
)
from comum import chave_comparacao, limpar_texto  # noqa: E402

AVISO = "Exemplo fictício — não representa resultados da PRF"

# ---------------------------------------------------------------------------
# ANTES: exatamente como os valores aparecem no arquivo bruto da PRF.
# ---------------------------------------------------------------------------
ANTES = [
    {
        "ref": "F01", "id": "F000001", "data_inversa": "2025-01-04",
        "dia_semana": "sábado", "horario": "23:40:00", "uf": "mg",
        "fase_dia": "Pleno dia", "sentido_via": "Crescente",
        "condicao_metereologica": "Céu Claro", "tipo_pista": "Simples",
        "tracado_via": "Reta", "uso_solo": "Sim",
        "classificacao_acidente": "Com Vítimas Feridas",
    },
    {
        "ref": "F02", "id": "F000002", "data_inversa": "2025-03-19",
        "dia_semana": "quarta-feira", "horario": "07:15:00", "uf": "PR",
        "fase_dia": "Amanhecer", "sentido_via": "Decrescente",
        "condicao_metereologica": "Chuva", "tipo_pista": "Múltipla",
        "tracado_via": "Reta;Declive", "uso_solo": "Não",
        "classificacao_acidente": "Sem Vítimas",
    },
    {
        "ref": "F03", "id": "F000003", "data_inversa": "2025-06-08",
        "dia_semana": "domingo", "horario": "03:05:00", "uf": "BA",
        "fase_dia": "Plena Noite", "sentido_via": "Crescente",
        "condicao_metereologica": "Ignorado", "tipo_pista": "Simples",
        "tracado_via": "Curva;Aclive", "uso_solo": "Não",
        "classificacao_acidente": "Com Vítimas Fatais",
    },
    {
        "ref": "F04", "id": "F000004", "data_inversa": "2025-09-22",
        "dia_semana": " segunda-feira ", "horario": "14:50:00", "uf": "sp",
        "fase_dia": "Pleno dia", "sentido_via": "Não Informado",
        "condicao_metereologica": "  Nublado ", "tipo_pista": "Dupla",
        "tracado_via": "Interseção de Vias;Reta", "uso_solo": "Sim",
        "classificacao_acidente": "Com Vítimas Feridas",
    },
    {
        "ref": "F05", "id": "F000005", "data_inversa": "2025-12-13",
        "dia_semana": "sábado", "horario": "18:30:00", "uf": "RS",
        "fase_dia": "Anoitecer", "sentido_via": "Decrescente",
        "condicao_metereologica": "Nevoeiro/Neblina", "tipo_pista": "Simples",
        "tracado_via": "Reta;Ponte", "uso_solo": "Não",
        "classificacao_acidente": "",
    },
]

COLUNAS_ANTES = [
    "ref", "id", "data_inversa", "dia_semana", "horario", "uf", "fase_dia",
    "sentido_via", "condicao_metereologica", "tipo_pista", "tracado_via",
    "uso_solo", "classificacao_acidente",
]

COLUNAS_DEPOIS = [
    "ref", "id", "data_inversa", "dia_semana", "horario", "uf", "mes", "mes_nome",
    "hora", "faixa_horaria", "fim_de_semana", "fase_dia", "sentido_via",
    "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
    "classificacao_acidente", "alvo_ausente", "elegivel_modelo",
]


def aplicar_transformacoes(df_antes: pd.DataFrame) -> pd.DataFrame:
    """Aplica exatamente as mesmas regras da limpeza real, uma a uma.

    Os mapas e funcoes vem de src/limpeza.py: nao ha regra paralela aqui, para o
    exemplo do slide nao contar uma historia diferente da execucao real.
    """
    d = df_antes.copy()

    # 1) limpeza de texto: espacos e caracteres invisiveis
    for c in d.columns:
        d[c] = d[c].map(limpar_texto)

    # 2) tokens de ausencia por coluna
    d["condicao_metereologica"] = d["condicao_metereologica"].where(
        d["condicao_metereologica"] != "Ignorado"
    )
    d["sentido_via"] = d["sentido_via"].where(d["sentido_via"] != "Não Informado")

    # 3) mapeamentos explicitos de categorias
    for coluna, mapa in (
        ("dia_semana", MAPA_DIA_SEMANA),
        ("uso_solo", MAPA_USO_SOLO),
        ("fase_dia", MAPA_FASE_DIA),
        ("tipo_pista", MAPA_TIPO_PISTA),
        ("condicao_metereologica", MAPA_CONDICAO),
        ("sentido_via", MAPA_SENTIDO),
    ):
        d[coluna] = d[coluna].map(
            lambda v, m=mapa: v if pd.isna(v) else m.get(chave_comparacao(v), v)
        )
    d["uf"] = d["uf"].str.upper()
    d["tracado_via"] = d["tracado_via"].map(canonizar_tracado)

    # 4) atributos derivados
    data = pd.to_datetime(d["data_inversa"], format="%Y-%m-%d", errors="coerce")
    d["mes"] = data.dt.month
    d["mes_nome"] = d["mes"].map(MESES)
    dia_calc = data.dt.dayofweek.map(DIA_SEMANA_POR_INDICE)
    d["fim_de_semana"] = dia_calc.isin(["Sábado", "Domingo"]).map({True: "Sim", False: "Não"})
    hora = pd.to_datetime(d["horario"], format="%H:%M:%S", errors="coerce")
    d["hora"] = hora.dt.hour
    d["faixa_horaria"] = d["hora"].map(lambda h: pd.NA if pd.isna(h) else faixa_da_hora(int(h)))

    # 5) sinalizacao do alvo: NUNCA imputado
    d["alvo_ausente"] = d["classificacao_acidente"].isna().map({True: "Sim", False: "Não"})
    d["elegivel_modelo"] = d["alvo_ausente"].map({"Sim": "Não", "Não": "Sim"})

    return d[COLUNAS_DEPOIS]


def salvar_imagem_tabela(df: pd.DataFrame, titulo: str, caminho, largura_col=1.6):
    """Desenha a tabela como imagem, para colar no slide sem virar print borrado."""
    n_lin, n_col = df.shape
    fig, ax = plt.subplots(figsize=(max(8, largura_col * n_col), 1.4 + 0.5 * n_lin))
    ax.axis("off")
    tabela = ax.table(
        cellText=df.fillna("(vazio)").astype(str).values,
        colLabels=df.columns, cellLoc="center", loc="center",
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(8)
    tabela.scale(1, 1.5)
    for j in range(n_col):
        tabela[(0, j)].set_facecolor("#1f3b57")
        tabela[(0, j)].set_text_props(color="white", weight="bold")
    for i in range(1, n_lin + 1):
        cor = "#f2f6fa" if i % 2 else "#ffffff"
        for j in range(n_col):
            tabela[(i, j)].set_facecolor(cor)
    ax.set_title(f"{titulo}\n{AVISO}", fontsize=11, weight="bold", pad=16)
    fig.tight_layout()
    fig.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    garantir_pastas()
    df_antes = pd.DataFrame(ANTES)[COLUNAS_ANTES]
    df_depois = aplicar_transformacoes(df_antes)

    df_antes.to_csv(DIR_REPORTS / "exemplo_antes.csv", sep=";", index=False,
                    encoding="utf-8-sig")
    df_depois.to_csv(DIR_REPORTS / "exemplo_depois.csv", sep=";", index=False,
                     encoding="utf-8-sig")

    # Colunas mais didaticas para a imagem (a tabela inteira nao cabe num slide).
    vitrine_antes = df_antes[[
        "ref", "dia_semana", "horario", "uf", "fase_dia", "condicao_metereologica",
        "tracado_via", "uso_solo", "sentido_via", "classificacao_acidente",
    ]]
    vitrine_depois = df_depois[[
        "ref", "dia_semana", "faixa_horaria", "fim_de_semana", "mes_nome", "uf",
        "fase_dia", "condicao_metereologica", "tracado_via", "uso_solo",
        "sentido_via", "classificacao_acidente", "elegivel_modelo",
    ]]
    salvar_imagem_tabela(vitrine_antes, "ANTES da padronizacao (base bruta)",
                         DIR_REPORTS / "exemplo_antes.png")
    salvar_imagem_tabela(vitrine_depois, "DEPOIS da padronizacao e dos derivados",
                         DIR_REPORTS / "exemplo_antes_depois.png")

    # ---- recorte da codificacao categorica (a futura matriz X) ----
    entradas = ["dia_semana", "faixa_horaria", "tipo_pista", "uso_solo"]
    codificado = pd.get_dummies(
        df_depois[entradas], prefix=entradas, dummy_na=False
    ).astype(int)
    # Mostra apenas algumas colunas, senao a imagem fica ilegivel.
    colunas_vitrine = [
        c for c in codificado.columns
        if c.startswith(("faixa_horaria_", "tipo_pista_", "uso_solo_"))
    ]
    recorte = pd.concat(
        [df_depois[["ref"]].reset_index(drop=True), codificado[colunas_vitrine]], axis=1
    )
    recorte.to_csv(DIR_REPORTS / "exemplo_codificacao.csv", sep=";", index=False,
                   encoding="utf-8-sig")
    salvar_imagem_tabela(recorte, "Recorte da codificacao categorica (one-hot) de X",
                         DIR_REPORTS / "exemplo_codificacao.png", largura_col=1.3)

    L = [f"# Tabela ANTES x DEPOIS (registros ficticios F01-F05)\n",
         f"> **{AVISO}**\n",
         "Estes cinco registros nao entram nos graficos reais, no treinamento nem "
         "nas metricas. Servem apenas para mostrar o efeito das regras.\n",
         "## O que cada registro demonstra\n",
         "| ref | problema exibido | regra aplicada |",
         "|---|---|---|",
         "| F01 | `dia_semana` em minusculas, `uso_solo` como \"Sim\", `fase_dia` como \"Pleno dia\", UF em minusculas | mapeamentos explicitos + UF em maiusculas |",
         "| F02 | `tracado_via` multivalorado fora de ordem (\"Reta;Declive\") | ordenacao alfabetica dos componentes |",
         "| F03 | `condicao_metereologica` = \"Ignorado\" (ausencia disfarcada de categoria) | token de ausencia por coluna |",
         "| F04 | espacos sobrando no texto e `sentido_via` = \"Nao Informado\" | limpeza de texto + token de ausencia |",
         "| F05 | `classificacao_acidente` vazia | alvo NAO imputado; registro fica inelegivel |",
         "",
         "## ANTES\n", tabela_markdown(vitrine_antes),
         "\n## DEPOIS\n", tabela_markdown(vitrine_depois),
         "\n## Recorte da codificacao categorica\n", tabela_markdown(recorte),
         "\n## Tres objetos diferentes\n",
         "- **base legivel** (`prf_limpo.csv`): rotulos em portugues, para ler e conferir.",
         "- **X transformado**: matriz numerica produzida pelo OneHotEncoder dentro do "
         "Pipeline, ajustada SOMENTE no treino. Nao e um arquivo para leitura humana.",
         "- **y**: apenas a coluna `classificacao_acidente` das linhas elegiveis.",
         "",
         "## Padronizacao de formato x normalizacao numerica\n",
         "- **Padronizar formato** e deixar data como `aaaa-mm-dd`, hora como `HH:MM:SS`, "
         "UF em maiusculas e categorias com grafia unica. E o que este projeto faz.",
         "- **Normalizar/padronizar escala** e transformar numeros para media 0 e desvio 1 "
         "(ou para o intervalo 0-1). Arvore de decisao NAO precisa disso, porque decide por "
         "limiares em cada atributo, sem comparar magnitudes entre colunas diferentes.",
         "",
         "## Limites das faixas horarias\n",
         "- Madrugada: 00:00:00 a 05:59:59",
         "- Manha: 06:00:00 a 11:59:59",
         "- Tarde: 12:00:00 a 17:59:59",
         "- Noite: 18:00:00 a 23:59:59",
         "",
         "> `faixa_horaria` e faixa de RELOGIO. `fase_dia` e a fase de luz registrada pelo "
         "policial (Amanhecer, Pleno Dia, Anoitecer, Plena Noite). Sao coisas diferentes: "
         "um acidente as 18:30 pode estar em \"Noite\" e, ao mesmo tempo, em \"Anoitecer\".\n",
         ]
    (DIR_REPORTS / "exemplo_ficticio.md").write_text("\n".join(L), encoding="utf-8")

    print("Arquivos gerados em reports/:")
    for nome in ("exemplo_antes.csv", "exemplo_depois.csv", "exemplo_antes.png",
                 "exemplo_antes_depois.png", "exemplo_codificacao.csv",
                 "exemplo_codificacao.png", "exemplo_ficticio.md"):
        print(f"  - {nome}")
    print(f"\n{AVISO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
