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
    calculado sobre poucos casos e instavel.

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
