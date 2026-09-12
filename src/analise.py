r"""
analise.py - ETAPA 6: analise descritiva, executada SOMENTE apos validacao.

Regra de bloqueio: este script chama o validador antes de qualquer grafico. Se uma
regra CRITICA reprovar, a analise nao roda. Isso evita produzir grafico bonito
sobre base furada.

O que e gerado, sempre com denominador visivel:
  - distribuicao das classes de gravidade (contagem e percentual);
  - composicao percentual da gravidade por faixa horaria, condicao meteorologica,
    tipo de pista, uso do solo, fase do dia e dia da semana;
  - marcacao de grupos pequenos (abaixo do minimo configuravel), porque percentual
    calculado sobre poucos casos e instavel;
  - variantes de visual para os slides: pizza, rosca, barras horizontais,
    barras agrupadas, heatmap e pizzas comparativas.

Cuidado interpretativo que aparece em todo relatorio: contagem de acidentes NAO e
risco por viagem. Sem dados de exposicao ao transito (quantos veiculos passaram,
por quanto tempo, em qual trecho), nao da para dizer que uma condicao "e mais
perigosa"; da para dizer apenas como os acidentes JA REGISTRADOS se distribuem.

Uso:
  python src\analise.py
  python src\analise.py --minimo-grupo 100
  python src\analise.py --pular-validacao      (nao recomendado; apenas para estudo)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

import validar_dados  # noqa: E402
from comum import (  # noqa: E402
    DIR_PROC,
    DIR_REPORTS,
    ambiente,
    carregar_contrato,
    garantir_pastas,
    hash_arquivo,
    salvar_json,
    tabela_markdown,
)

ORDEM_CLASSES = ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"]
ORDEM_FAIXA = ["Madrugada", "Manhã", "Tarde", "Noite"]
ORDEM_DIA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
             "Sexta-feira", "Sábado", "Domingo"]
ORDEM_FASE = ["Amanhecer", "Pleno Dia", "Anoitecer", "Plena Noite"]

CORES = {"Sem Vítimas": "#4c78a8", "Com Vítimas Feridas": "#f58518",
         "Com Vítimas Fatais": "#b3271e"}

DIR_FIG = DIR_REPORTS / "figuras"

AVISO_RISCO = (
    "Contagem de acidentes registrados. NAO e risco por viagem: nao ha dados de "
    "exposicao ao transito nesta base."
)


def ordenar_categorias(valores, ordem_preferida):
    """Mantem a ordem didatica quando conhecida; o resto entra por frequencia."""
    conhecidos = [v for v in ordem_preferida if v in valores]
    resto = sorted(v for v in valores if v not in conhecidos)
    return conhecidos + resto


def tabela_cruzada(df: pd.DataFrame, coluna: str, minimo_grupo: int) -> pd.DataFrame:
    """Composicao percentual da gravidade dentro de cada categoria de 'coluna'.

    O percentual e SEMPRE por linha (dentro do grupo) e vem acompanhado do
    denominador, para nao virar numero solto no slide.
    """
    dados = df[[coluna, "classificacao_acidente"]].copy()
    dados[coluna] = dados[coluna].fillna("(ausente)")
    cont = pd.crosstab(dados[coluna], dados["classificacao_acidente"])
    for classe in ORDEM_CLASSES:
        if classe not in cont.columns:
            cont[classe] = 0
    cont = cont[[c for c in ORDEM_CLASSES if c in cont.columns]]
    cont["total_no_grupo"] = cont.sum(axis=1)
    for classe in ORDEM_CLASSES:
        cont[f"pct_{classe}"] = (100 * cont[classe] / cont["total_no_grupo"]).round(2)
    cont["grupo_pequeno"] = (cont["total_no_grupo"] < minimo_grupo).map(
        {True: "Sim", False: "Não"}
    )
    cont["pct_do_total_de_acidentes"] = (
        100 * cont["total_no_grupo"] / cont["total_no_grupo"].sum()
    ).round(2)
    cont.index.name = coluna
    ordem = ordenar_categorias(
        list(cont.index),
        {"faixa_horaria": ORDEM_FAIXA, "dia_semana": ORDEM_DIA, "fase_dia": ORDEM_FASE}
        .get(coluna, []),
    )
    return cont.loc[ordem]


def grafico_composicao(tab: pd.DataFrame, coluna: str, titulo: str, caminho: Path,
                       minimo_grupo: int) -> None:
    """Barras 100% empilhadas: composicao da gravidade dentro de cada grupo."""
    pcts = tab[[f"pct_{c}" for c in ORDEM_CLASSES if f"pct_{c}" in tab.columns]]
    fig, ax = plt.subplots(figsize=(max(7, 1.1 * len(tab)), 5.2))
    base = pd.Series(0.0, index=tab.index)
    for classe in ORDEM_CLASSES:
        col = f"pct_{classe}"
        if col not in pcts.columns:
            continue
        ax.bar(tab.index.astype(str), pcts[col], bottom=base,
               label=classe, color=CORES[classe], edgecolor="white")
        base = base + pcts[col]
    rotulos = [
        f"{idx}\nn={int(tot)}" + ("\n(grupo pequeno)" if tot < minimo_grupo else "")
        for idx, tot in zip(tab.index.astype(str), tab["total_no_grupo"])
    ]
    ax.set_xticks(range(len(tab)))
    ax.set_xticklabels(rotulos, fontsize=8)
    ax.set_ylabel("Composição percentual dentro do grupo (%)")
    ax.set_ylim(0, 100)
    ax.set_title(titulo, fontsize=12, weight="bold")
    ax.legend(title="Gravidade", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.text(0.01, -0.02, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_distribuicao_classes(df: pd.DataFrame, caminho: Path) -> pd.DataFrame:
    cont = df["classificacao_acidente"].value_counts(dropna=False)
    cont.index = [("(ausente)" if pd.isna(i) else i) for i in cont.index]
    tab = pd.DataFrame({"acidentes": cont})
    tab["pct"] = (100 * tab["acidentes"] / tab["acidentes"].sum()).round(3)
    ordem = ordenar_categorias(list(tab.index), ORDEM_CLASSES)
    tab = tab.loc[ordem]

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    cores = [CORES.get(i, "#888888") for i in tab.index]
    barras = ax.bar(tab.index.astype(str), tab["acidentes"], color=cores)
    for barra, (n, pct) in zip(barras, tab[["acidentes", "pct"]].values):
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
                f"{int(n)}\n({pct}%)", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Ocorrências registradas")
    ax.set_title(f"Distribuição da gravidade — {int(tab['acidentes'].sum())} ocorrências",
                 fontsize=12, weight="bold")
    ax.set_ylim(0, tab["acidentes"].max() * 1.18)
    fig.text(0.01, -0.03, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return tab


# ---------------------------------------------------------------------------
# Variantes para os slides. Os graficos acima continuam sendo a referencia
# principal; estes existem para dar opcao de visual (pizza, rosca, barras
# horizontais, agrupadas e heatmap) sem mudar o significado dos numeros.
# ---------------------------------------------------------------------------

def _classes_sem_ausente(tab: pd.DataFrame) -> pd.DataFrame:
    """Tira a linha '(ausente)' da pizza: 1 caso em 72 mil nao cabe no slide."""
    return tab.loc[[i for i in tab.index if i != "(ausente)"]]


def grafico_pizza_gravidade(tab: pd.DataFrame, caminho: Path) -> None:
    """Pizza da gravidade: melhor leitura da proporcao do desbalanceamento."""
    dados = _classes_sem_ausente(tab)
    cores = [CORES.get(i, "#888888") for i in dados.index]
    total = int(dados["acidentes"].sum())

    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    fatias, _, autotextos = ax.pie(
        dados["acidentes"],
        labels=None,
        colors=cores,
        startangle=90,
        explode=[0.02] * len(dados),
        wedgeprops={"linewidth": 1.2, "edgecolor": "white"},
        autopct=lambda p: f"{p:.1f}%",
        pctdistance=0.72,
    )
    for t in autotextos:
        t.set_fontsize(10)
        t.set_color("white")
        t.set_weight("bold")
    ax.legend(
        fatias,
        [f"{nome}\n{int(n):,} ocorrências".replace(",", ".") for nome, n in
         zip(dados.index, dados["acidentes"])],
        title="Gravidade",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=9,
    )
    ax.set_title(f"Participação de cada gravidade — {total:,} ocorrências".replace(",", "."),
                 fontsize=12, weight="bold")
    fig.text(0.01, 0.01, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_rosca_gravidade(tab: pd.DataFrame, caminho: Path) -> None:
    """Rosca: mesma pizza, com o total no centro — fica limpa no slide."""
    dados = _classes_sem_ausente(tab)
    cores = [CORES.get(i, "#888888") for i in dados.index]
    total = int(dados["acidentes"].sum())

    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    fatias, _, autotextos = ax.pie(
        dados["acidentes"],
        labels=None,
        colors=cores,
        startangle=90,
        wedgeprops={"width": 0.42, "linewidth": 1.2, "edgecolor": "white"},
        autopct=lambda p: f"{p:.1f}%",
        pctdistance=0.78,
    )
    for t in autotextos:
        t.set_fontsize(10)
        t.set_weight("bold")
    ax.text(0, 0, f"{total:,}\nocorrências".replace(",", "."),
            ha="center", va="center", fontsize=13, weight="bold")
    ax.legend(
        fatias, list(dados.index), title="Gravidade",
        loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9,
    )
    ax.set_title("Rosca da distribuição de gravidade", fontsize=12, weight="bold")
    fig.text(0.01, 0.01, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_barras_horizontais(serie: pd.Series, titulo: str, caminho: Path,
                               cor: str = "#4c78a8") -> None:
    """Volume absoluto de ocorrencias: barras horizontais, com n e % no rotulo."""
    serie = serie.sort_values(ascending=True)
    total = int(serie.sum())
    fig, ax = plt.subplots(figsize=(8.5, max(3.8, 0.45 * len(serie) + 1.2)))
    barras = ax.barh(serie.index.astype(str), serie.values, color=cor, edgecolor="white")
    for barra, n in zip(barras, serie.values):
        pct = 100 * n / total
        ax.text(barra.get_width() + total * 0.008, barra.get_y() + barra.get_height() / 2,
                f"{int(n):,}  ({pct:.1f}%)".replace(",", "."),
                va="center", fontsize=8)
    ax.set_xlabel("Ocorrências registradas")
    ax.set_xlim(0, serie.max() * 1.28)
    ax.set_title(f"{titulo} — total {total:,}".replace(",", "."),
                 fontsize=12, weight="bold")
    fig.text(0.01, -0.02, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_barras_agrupadas(tab: pd.DataFrame, titulo: str, caminho: Path,
                             minimo_grupo: int) -> None:
    """Contagens absolutas lado a lado: complementa as barras 100% empilhadas.

    As empilhadas mostram COMPOSICAO; estas mostram VOLUME. As duas juntas
    evitam a confusao de achar que um grupo 'tem mais fatais' so porque a fatia
    vermelha parece maior em um n pequeno.
    """
    classes = [c for c in ORDEM_CLASSES if c in tab.columns]
    x = range(len(tab))
    largura = 0.8 / max(len(classes), 1)
    fig, ax = plt.subplots(figsize=(max(8, 1.3 * len(tab)), 5.4))
    for i, classe in enumerate(classes):
        desloc = -0.4 + largura / 2 + i * largura
        ax.bar([p + desloc for p in x], tab[classe].values, width=largura,
               label=classe, color=CORES[classe], edgecolor="white")
    rotulos = [
        f"{idx}\nn={int(tot)}" + ("\n(pequeno)" if tot < minimo_grupo else "")
        for idx, tot in zip(tab.index.astype(str), tab["total_no_grupo"])
    ]
    ax.set_xticks(list(x))
    ax.set_xticklabels(rotulos, fontsize=8)
    ax.set_ylabel("Ocorrências registradas")
    ax.set_title(titulo, fontsize=12, weight="bold")
    ax.legend(title="Gravidade", fontsize=8)
    fig.text(0.01, -0.02, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_heatmap(tab: pd.DataFrame, titulo: str, caminho: Path) -> None:
    """Mapa de calor do percentual de cada gravidade dentro do grupo."""
    cols = [f"pct_{c}" for c in ORDEM_CLASSES if f"pct_{c}" in tab.columns]
    if not cols:
        return
    matriz = tab[cols].copy()
    matriz.columns = [c.replace("pct_", "") for c in cols]

    fig, ax = plt.subplots(figsize=(max(7.5, 0.9 * len(matriz.columns) + 4),
                                    max(4.2, 0.45 * len(matriz) + 1.5)))
    sns.heatmap(
        matriz.astype(float), annot=True, fmt=".1f", cmap="YlOrRd",
        linewidths=0.6, linecolor="white", cbar_kws={"label": "% dentro do grupo"},
        ax=ax,
    )
    ax.set_xlabel("Gravidade")
    ax.set_ylabel(tab.index.name or "")
    ax.set_title(titulo, fontsize=12, weight="bold")
    fig.text(0.01, -0.02, AVISO_RISCO + " Valores em % dentro de cada linha.",
             fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def grafico_pizza_comparativa(df: pd.DataFrame, coluna: str, titulo: str,
                              caminho: Path, ordem: list[str] | None = None,
                              rotulos: dict[str, str] | None = None) -> None:
    """Duas ou tres pizzas lado a lado: composicao da gravidade em cada categoria.

    So faz sentido com poucas categorias (uso do solo, fim de semana, tipo de
    pista). Com muitas fatias vira ilegivel — por isso nao uso em dia_semana.
    """
    dados = df[[coluna, "classificacao_acidente"]].dropna().copy()
    cats = ordenar_categorias(list(dados[coluna].unique()), ordem or [])
    if not cats:
        return
    mapa_rotulo = rotulos or {}
    fig, eixos = plt.subplots(1, len(cats), figsize=(4.2 * len(cats), 4.8))
    if len(cats) == 1:
        eixos = [eixos]
    for ax, cat in zip(eixos, cats):
        cont = dados.loc[dados[coluna] == cat, "classificacao_acidente"].value_counts()
        cont = cont.reindex([c for c in ORDEM_CLASSES if c in cont.index])
        cores = [CORES[c] for c in cont.index]
        n = int(cont.sum())
        ax.pie(
            cont.values, colors=cores, startangle=90,
            wedgeprops={"linewidth": 1, "edgecolor": "white", "width": 0.55},
            autopct=lambda p: f"{p:.0f}%" if p >= 4 else "",
            pctdistance=0.75,
        )
        nome = mapa_rotulo.get(cat, cat)
        ax.set_title(f"{nome}\nn = {n:,}".replace(",", "."), fontsize=10, weight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CORES[c]) for c in ORDEM_CLASSES]
    fig.legend(handles, ORDEM_CLASSES, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(titulo, fontsize=12, weight="bold", y=1.02)
    fig.text(0.01, -0.06, AVISO_RISCO, fontsize=7, style="italic")
    fig.tight_layout()
    fig.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="Analise descritiva da base limpa.")
    ap.add_argument("--arquivo", default=str(DIR_PROC / "prf_limpo.csv"))
    ap.add_argument("--minimo-grupo", type=int, default=200,
                    help="Abaixo deste n o grupo e marcado como pequeno.")
    ap.add_argument("--pular-validacao", action="store_true")
    args = ap.parse_args()

    garantir_pastas()
    DIR_FIG.mkdir(parents=True, exist_ok=True)
    contrato = carregar_contrato()
    arquivo = Path(args.arquivo)
    if not arquivo.exists():
        print(f"[ERRO] Base limpa nao encontrada: {arquivo}. Rode src\\limpeza.py antes.")
        return 2

    # ---- BLOQUEIO: nao analisa base reprovada em regra critica ----
    if args.pular_validacao:
        print("[AVISO] Validacao pulada por opcao do usuario. Nao recomendado.")
        status_validacao = "NAO EXECUTADA (pulada por --pular-validacao)"
    else:
        print("[1/3] Revalidando a base antes de analisar...")
        codigo = validar_dados.main(["--arquivo", str(arquivo), "--silencioso"])
        import json

        rel = json.loads((DIR_REPORTS / "validacao.json").read_text(encoding="utf-8"))
        status_validacao = rel["status_global"]
        print(f"      status da validacao: {status_validacao} (codigo {codigo})")
        if codigo != 0:
            print("[BLOQUEADO] A base falhou em regra critica. Analise interrompida.")
            print("            Veja reports/validacao.md e corrija antes de seguir.")
            return 1

    print("[2/3] Lendo a base limpa e montando tabelas...")
    df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str)
    # Somente para a analise: valores vazios viram ausencia explicita.
    df = df.replace({"": pd.NA})

    sns.set_theme(style="whitegrid")
    tab_classes = grafico_distribuicao_classes(df, DIR_FIG / "01_distribuicao_classes.png")
    tab_classes.to_csv(DIR_REPORTS / "tabela_distribuicao_classes.csv", sep=";",
                       encoding="utf-8-sig")

    # A composicao por grupo usa apenas ocorrencias com alvo conhecido: nao da para
    # calcular percentual de gravidade em linha cujo alvo esta vazio.
    com_alvo = df[df["classificacao_acidente"].notna()]

    recortes = {
        "faixa_horaria": "Gravidade por faixa horária (relógio)",
        "condicao_metereologica": "Gravidade por condição meteorológica",
        "tipo_pista": "Gravidade por tipo de pista",
        "uso_solo": "Gravidade por uso do solo",
        "fase_dia": "Gravidade por fase do dia (registro da PRF)",
        "dia_semana": "Gravidade por dia da semana",
        "fim_de_semana": "Gravidade em fim de semana",
    }
    tabelas = {}
    for i, (coluna, titulo) in enumerate(recortes.items(), start=2):
        if coluna not in com_alvo.columns:
            print(f"      [pulado] coluna ausente: {coluna}")
            continue
        tab = tabela_cruzada(com_alvo, coluna, args.minimo_grupo)
        tabelas[coluna] = tab
        tab.to_csv(DIR_REPORTS / f"tabela_gravidade_por_{coluna}.csv", sep=";",
                   encoding="utf-8-sig")
        grafico_composicao(tab, coluna, titulo,
                           DIR_FIG / f"{i:02d}_gravidade_por_{coluna}.png",
                           args.minimo_grupo)
        print(f"      tabela e grafico: {coluna}")

    print("      gerando variantes de visual para os slides...")
    grafico_pizza_gravidade(tab_classes, DIR_FIG / "09_pizza_gravidade.png")
    grafico_rosca_gravidade(tab_classes, DIR_FIG / "10_rosca_gravidade.png")

    # Volumes absolutos: barras horizontais (leitura mais facil no projetor)
    ordem_dia = ordenar_categorias(list(com_alvo["dia_semana"].dropna().unique()), ORDEM_DIA)
    vol_dia = com_alvo["dia_semana"].value_counts().reindex(ordem_dia)
    grafico_barras_horizontais(
        vol_dia, "Volume de ocorrências por dia da semana",
        DIR_FIG / "11_barras_horizontais_dia_semana.png", cor="#4c78a8",
    )
    ordem_faixa = ordenar_categorias(
        list(com_alvo["faixa_horaria"].dropna().unique()), ORDEM_FAIXA
    )
    vol_faixa = com_alvo["faixa_horaria"].value_counts().reindex(ordem_faixa)
    grafico_barras_horizontais(
        vol_faixa, "Volume de ocorrências por faixa horária",
        DIR_FIG / "12_barras_horizontais_faixa_horaria.png", cor="#f58518",
    )
    # Condicao meteorologica: so as categorias com volume razoavel no slide
    vol_clima = com_alvo["condicao_metereologica"].fillna("(ausente)").value_counts()
    vol_clima = vol_clima[vol_clima >= args.minimo_grupo].sort_values(ascending=True)
    grafico_barras_horizontais(
        vol_clima, "Volume de ocorrências por condição meteorológica",
        DIR_FIG / "13_barras_horizontais_clima.png", cor="#54a24b",
    )

    # Barras agrupadas e heatmap: composicao + volume lado a lado
    if "tipo_pista" in tabelas:
        grafico_barras_agrupadas(
            tabelas["tipo_pista"],
            "Contagem absoluta da gravidade por tipo de pista",
            DIR_FIG / "14_barras_agrupadas_tipo_pista.png",
            args.minimo_grupo,
        )
    if "faixa_horaria" in tabelas:
        grafico_heatmap(
            tabelas["faixa_horaria"],
            "Mapa de calor: % de cada gravidade por faixa horária",
            DIR_FIG / "15_heatmap_faixa_horaria.png",
        )
    if "dia_semana" in tabelas:
        grafico_heatmap(
            tabelas["dia_semana"],
            "Mapa de calor: % de cada gravidade por dia da semana",
            DIR_FIG / "16_heatmap_dia_semana.png",
        )

    # Pizzas comparativas: so onde ha poucas categorias
    grafico_pizza_comparativa(
        com_alvo, "uso_solo",
        "Composição da gravidade por uso do solo",
        DIR_FIG / "17_pizzas_uso_solo.png",
        ordem=["Urbano", "Rural"],
    )
    grafico_pizza_comparativa(
        com_alvo, "fim_de_semana",
        "Composição da gravidade: dia útil × fim de semana",
        DIR_FIG / "18_pizzas_fim_de_semana.png",
        ordem=["Não", "Sim"],
        rotulos={"Não": "Dia útil", "Sim": "Fim de semana"},
    )
    grafico_pizza_comparativa(
        com_alvo, "tipo_pista",
        "Composição da gravidade por tipo de pista",
        DIR_FIG / "19_pizzas_tipo_pista.png",
        ordem=["Simples", "Dupla", "Múltipla"],
    )
    print("      variantes salvas em reports/figuras/ (09 a 19)")

    print("[3/3] Escrevendo relatorio da analise...")
    resumo = {
        "ambiente": ambiente(),
        "arquivo_analisado": str(arquivo),
        "sha256": hash_arquivo(arquivo),
        "status_da_validacao_antes_da_analise": status_validacao,
        "versao_contrato": contrato["versao_contrato"],
        "fonte": contrato["fonte"],
        "filtros_aplicados": [
            "Nenhuma linha foi excluida da base limpa.",
            "As tabelas de composicao por grupo usam apenas ocorrencias com "
            "classificacao_acidente preenchida, porque nao existe percentual de "
            "gravidade para alvo ausente.",
        ],
        "minimo_grupo": args.minimo_grupo,
        "ocorrencias_na_base": int(len(df)),
        "ocorrencias_com_alvo": int(len(com_alvo)),
        "distribuicao_classes": tab_classes.reset_index().rename(
            columns={"index": "classificacao_acidente"}
        ).to_dict(orient="records"),
        "aviso_interpretativo": AVISO_RISCO,
        "limitacoes": contrato["limitacoes_da_auditoria"],
    }
    salvar_json(resumo, DIR_REPORTS / "analise.json")

    L = ["# Analise descritiva da base limpa\n",
         f"- Arquivo: `{arquivo}`",
         f"- SHA-256: `{resumo['sha256']}`",
         f"- Status da validacao antes da analise: **{status_validacao}**",
         f"- Periodo declarado: {contrato['fonte']['periodo_declarado']}",
         f"- Ocorrencias na base: {len(df)} | com alvo preenchido: {len(com_alvo)}",
         f"- Grupo considerado pequeno abaixo de n = {args.minimo_grupo}",
         f"- Execucao: {resumo['ambiente']['executado_em']}\n",
         f"> {AVISO_RISCO}\n",
         "## Filtros aplicados\n"]
    L += [f"- {t}" for t in resumo["filtros_aplicados"]]
    L.append("\n## Distribuicao das classes\n")
    L.append(tabela_markdown(tab_classes.reset_index().rename(columns={"index": "gravidade"})))
    L.append("\n![Distribuicao das classes](figuras/01_distribuicao_classes.png)\n")
    for i, (coluna, titulo) in enumerate(recortes.items(), start=2):
        if coluna not in tabelas:
            continue
        L.append(f"## {titulo}\n")
        L.append(tabela_markdown(tabelas[coluna].reset_index()))
        L.append(f"\n![{titulo}](figuras/{i:02d}_gravidade_por_{coluna}.png)\n")

    L.append("## Variantes de visual para os slides\n")
    L.append("Os graficos acima sao a referencia principal (barras e barras 100% "
             "empilhadas). As figuras abaixo sao **variacoes de estilo** com os "
             "mesmos numeros, pensadas para o projetor:\n")
    L.append("| arquivo | quando usar |")
    L.append("|---|---|")
    L.append("| `09_pizza_gravidade.png` | mostrar o desbalanceamento das classes |")
    L.append("| `10_rosca_gravidade.png` | mesma pizza, com o total no centro |")
    L.append("| `11_barras_horizontais_dia_semana.png` | volume por dia da semana |")
    L.append("| `12_barras_horizontais_faixa_horaria.png` | volume por faixa horaria |")
    L.append("| `13_barras_horizontais_clima.png` | volume por clima (grupos pequenos omitidos) |")
    L.append("| `14_barras_agrupadas_tipo_pista.png` | volume absoluto (nao percentual) por tipo de pista |")
    L.append("| `15_heatmap_faixa_horaria.png` / `16_heatmap_dia_semana.png` | comparar % de cada gravidade em uma tabela visual |")
    L.append("| `17_pizzas_uso_solo.png` / `18_pizzas_fim_de_semana.png` / `19_pizzas_tipo_pista.png` | comparar composicao entre poucas categorias |\n")
    L.append("![Pizza da gravidade](figuras/09_pizza_gravidade.png)\n")
    L.append("![Rosca da gravidade](figuras/10_rosca_gravidade.png)\n")
    L.append("![Barras horizontais — dia da semana](figuras/11_barras_horizontais_dia_semana.png)\n")
    L.append("![Barras horizontais — faixa horaria](figuras/12_barras_horizontais_faixa_horaria.png)\n")
    L.append("![Barras horizontais — clima](figuras/13_barras_horizontais_clima.png)\n")
    L.append("![Barras agrupadas — tipo de pista](figuras/14_barras_agrupadas_tipo_pista.png)\n")
    L.append("![Heatmap — faixa horaria](figuras/15_heatmap_faixa_horaria.png)\n")
    L.append("![Heatmap — dia da semana](figuras/16_heatmap_dia_semana.png)\n")
    L.append("![Pizzas — uso do solo](figuras/17_pizzas_uso_solo.png)\n")
    L.append("![Pizzas — fim de semana](figuras/18_pizzas_fim_de_semana.png)\n")
    L.append("![Pizzas — tipo de pista](figuras/19_pizzas_tipo_pista.png)\n")

    L.append("## Como ler estes numeros\n")
    L.append("- `total_no_grupo` e o denominador: o percentual de cada classe e "
             "calculado DENTRO do grupo.")
    L.append("- `grupo_pequeno = Sim` significa que o percentual vem de poucos casos e "
             "pode variar muito; nao serve para conclusao.")
    L.append("- Diferenca de composicao entre grupos e ASSOCIACAO observada nos registros, "
             "nao causa nem probabilidade de acidente por viagem.")
    L.append("- Grupos com `(ausente)` mostram quanta informacao faltava, em vez de "
             "esconder a ausencia.\n")
    L.append("## Limitacoes\n")
    L += [f"- {t}" for t in contrato["limitacoes_da_auditoria"]]
    (DIR_REPORTS / "analise.md").write_text("\n".join(L), encoding="utf-8")

    print()
    print("=" * 72)
    print(f"Analise concluida. Figuras em {DIR_FIG}")
    print(f"Relatorio: {DIR_REPORTS / 'analise.md'}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
