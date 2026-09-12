r"""
treinar_modelo.py - ETAPA 7 (OPCIONAL): mineracao como complemento de estudo.

Este script fica em comando separado de proposito. O trabalho pede o PLANEJAMENTO
do KDD; o modelo aqui e complemento, e nada nos slides depende de ele ter rodado.

Escolhas e por que:

  * Arvore de decisao de classificacao. A tarefa e categorica (tres classes de
    gravidade) e a arvore permite LER as regras aprendidas, o que e essencial num
    trabalho didatico. Profundidade limitada para nao decorar a base.

  * random_state=42 em tudo que sorteia, para o resultado ser reproduzivel.

  * DummyClassifier(strategy="most_frequent") como referencia. Como 77% das
    ocorrencias sao "Com Vitimas Feridas", um chute fixo nessa classe ja acerta
    77%. Sem essa comparacao, "77% de acuracia" pareceria bom e nao seria.

  * Divisao 80/20 ESTRATIFICADA feita ANTES de qualquer transformacao aprendida.
    O OneHotEncoder e o imputador vivem dentro de um Pipeline e sao ajustados
    SOMENTE no treino (fit no treino, transform no teste). Isso evita vazamento:
    se o encoder visse o teste, o modelo teria informacao que nao deveria ter.

  * handle_unknown="ignore" no OneHotEncoder: se uma categoria aparecer apenas no
    teste, ela vira um vetor de zeros em vez de quebrar a execucao.

  * Escolha de max_depth por validacao cruzada NO TREINO. O conjunto de teste nao
    participa da escolha de parametro nenhum.

  * Arvore NAO precisa de padronizacao de escala. Ela decide por limiares dentro de
    cada atributo separadamente, sem comparar magnitudes entre colunas. Padronizar
    FORMATO (data, hora, categoria) e outra coisa, e isso foi feito na limpeza.

  * Metricas: matriz de confusao, precisao/recall/F1 por classe com suporte,
    macro-F1 e acuracia balanceada. Acuracia global e apenas complementar, porque
    com classes desbalanceadas ela premia quem so acerta a classe maioritaria.

O que NAO se pode concluir daqui: nada sobre causa, nem sobre probabilidade de uma
viagem sofrer acidente, nem sobre periodos futuros. As regras extraidas da arvore
sao padroes do MODELO sobre acidentes JA REGISTRADOS.

Uso:
  python src\treinar_modelo.py
  python src\treinar_modelo.py --balanceado
  python src\treinar_modelo.py --profundidades 3 4 5 6 8 --pular-validacao
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.dummy import DummyClassifier  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    ConfusionMatrixDisplay,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder  # noqa: E402
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree  # noqa: E402

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

SEMENTE = 42
DIR_MODELO = DIR_REPORTS / "modelo"

ORDEM_CLASSES = ["Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Treino OPCIONAL de arvore de decisao para a gravidade do acidente."
    )
    ap.add_argument("--arquivo", default=str(DIR_PROC / "prf_limpo.csv"))
    ap.add_argument("--profundidades", type=int, nargs="+", default=[3, 4, 5, 6, 8, 10],
                    help="Valores de max_depth testados por validacao cruzada NO TREINO.")
    ap.add_argument("--balanceado", action="store_true",
                    help="Usa class_weight='balanced' (justificado pelo desbalanceamento).")
    ap.add_argument("--minimo-por-classe", type=int, default=50,
                    help="Suporte minimo por classe para considerar o treino viavel.")
    ap.add_argument("--pular-validacao", action="store_true")
    args = ap.parse_args()

    garantir_pastas()
    # A variante balanceada grava em pasta propria, para poder comparar as duas
    # execucoes sem que uma sobrescreva a outra.
    global DIR_MODELO
    if args.balanceado:
        DIR_MODELO = DIR_REPORTS / "modelo_balanceado"
    DIR_MODELO.mkdir(parents=True, exist_ok=True)
    contrato = carregar_contrato()
    arquivo = Path(args.arquivo)
    if not arquivo.exists():
        print(f"[ERRO] Base limpa nao encontrada: {arquivo}. Rode src\\limpeza.py antes.")
        return 2

    # ---- BLOQUEIO: nao treina sobre base reprovada em regra critica ----
    if args.pular_validacao:
        print("[AVISO] Validacao pulada por opcao do usuario.")
        status_validacao = "NAO EXECUTADA (pulada por --pular-validacao)"
    else:
        print("[1/6] Revalidando a base antes de treinar...")
        codigo = validar_dados.main(["--arquivo", str(arquivo), "--silencioso"])
        rel = json.loads((DIR_REPORTS / "validacao.json").read_text(encoding="utf-8"))
        status_validacao = rel["status_global"]
        print(f"      status da validacao: {status_validacao} (codigo {codigo})")
        if codigo != 0:
            print("[BLOQUEADO] Base reprovada em regra critica. Treino interrompido.")
            return 1

    # ---- selecao de X e y a partir do CONTRATO, nao por exclusao ----
    print("[2/6] Selecionando entradas permitidas e o alvo...")
    entradas = list(contrato["entradas_modelo_permitidas"])
    alvo = contrato["alvo"]["coluna"]

    df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str).replace({"": pd.NA})
    faltando = [c for c in entradas + [alvo, "elegivel_modelo", "id"] if c not in df.columns]
    if faltando:
        print(f"[ERRO] Colunas necessarias ausentes na base limpa: {faltando}")
        return 2

    # Somente linhas elegiveis: alvo ausente NUNCA e imputado.
    elegiveis = df[df["elegivel_modelo"] == "Sim"].copy()
    excluidas = len(df) - len(elegiveis)

    # 'mes' e a unica entrada numerica; tratamos como categoria ordenada por
    # simplicidade didatica (12 valores discretos), junto das demais categoricas.
    # O SimpleImputer do scikit-learn nao entende o pd.NA do dtype 'string',
    # por isso X vai como object com numpy.nan marcando a ausencia.
    bruto_X = elegiveis[entradas]
    X = bruto_X.astype(object).where(bruto_X.notna(), np.nan)
    y = elegiveis[alvo].astype(str)
    ids = elegiveis["id"].astype(str)

    suporte = y.value_counts().to_dict()
    print(f"      elegiveis: {len(elegiveis)} | excluidas por alvo ausente: {excluidas}")
    print(f"      suporte por classe: {suporte}")
    insuficientes = {k: v for k, v in suporte.items() if v < args.minimo_por_classe}
    if insuficientes:
        print(f"[LIMITACAO] Classes com suporte abaixo de {args.minimo_por_classe}: "
              f"{insuficientes}. O resultado para essas classes nao e confiavel.")
    if len(suporte) < 2:
        print("[BLOQUEADO] Menos de duas classes com dados. Classificacao impossivel.")
        return 1

    # ---- divisao ANTES de qualquer transformacao aprendida ----
    print("[3/6] Separando treino e teste (80/20 estratificado, antes de transformar)...")
    X_treino, X_teste, y_treino, y_teste, id_treino, id_teste = train_test_split(
        X, y, ids, test_size=0.20, stratify=y, random_state=SEMENTE
    )
    vazamento_ids = set(id_treino) & set(id_teste)
    print(f"      treino: {len(X_treino)} | teste: {len(X_teste)}")
    print(f"      ocorrencias em ambos os conjuntos: {len(vazamento_ids)}")
    if vazamento_ids:
        print("[BLOQUEADO] A mesma ocorrencia apareceu no treino e no teste.")
        return 1

    # ---- pipeline: imputacao e one-hot ajustados SOMENTE no treino ----
    print("[4/6] Ajustando o Pipeline apenas com os dados de treino...")
    pre = ColumnTransformer(
        transformers=[(
            "categoricas",
            Pipeline([
                # Ausencia em ENTRADA vira a categoria explicita "(ausente)".
                # Isso e melhor que a moda: preserva a informacao "nao foi informado"
                # em vez de fingir que era o valor mais comum.
                ("imputar", SimpleImputer(strategy="constant", fill_value="(ausente)")),
                ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]),
            entradas,
        )],
        remainder="drop",  # nada entra em X por acidente
    )

    arvore = DecisionTreeClassifier(
        random_state=SEMENTE,
        class_weight="balanced" if args.balanceado else None,
        min_samples_leaf=50,  # folha minima: evita regra apoiada em pouquissimos casos
    )
    pipe = Pipeline([("pre", pre), ("arvore", arvore)])

    # max_depth escolhido por validacao cruzada DENTRO DO TREINO.
    busca = GridSearchCV(
        pipe,
        param_grid={"arvore__max_depth": args.profundidades},
        scoring="f1_macro",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE),
        n_jobs=-1,
        refit=True,
    )
    busca.fit(X_treino, y_treino)
    melhor = busca.best_estimator_
    print(f"      max_depth escolhido por CV no treino: "
          f"{busca.best_params_['arvore__max_depth']} (macro-F1 CV = {busca.best_score_:.4f})")

    # ---- referencia ----
    referencia = DummyClassifier(strategy="most_frequent", random_state=SEMENTE)
    referencia.fit(X_treino, y_treino)

    # ---- avaliacao no teste, uma unica vez ----
    print("[5/6] Avaliando no conjunto de teste...")
    rotulos = [c for c in ORDEM_CLASSES if c in set(y)]

    def avaliar(modelo, nome: str) -> dict:
        pred = modelo.predict(X_teste)
        rep = classification_report(
            y_teste, pred, labels=rotulos, output_dict=True, zero_division=0
        )
        return {
            "modelo": nome,
            "acuracia_global": round(rep["accuracy"], 4),
            "acuracia_balanceada": round(balanced_accuracy_score(y_teste, pred), 4),
            "macro_f1": round(f1_score(y_teste, pred, average="macro", zero_division=0), 4),
            "por_classe": {
                c: {
                    "precisao": round(rep[c]["precision"], 4),
                    "recall": round(rep[c]["recall"], 4),
                    "f1": round(rep[c]["f1-score"], 4),
                    "suporte": int(rep[c]["support"]),
                }
                for c in rotulos
            },
            "matriz_confusao": confusion_matrix(y_teste, pred, labels=rotulos).tolist(),
            "predicao": pred,
        }

    res_arvore = avaliar(melhor, "Arvore de decisao")
    res_dummy = avaliar(referencia, "DummyClassifier (most_frequent)")

    # ---- figuras ----
    fig, ax = plt.subplots(figsize=(6.8, 5.6))
    ConfusionMatrixDisplay.from_predictions(
        y_teste, res_arvore.pop("predicao"), labels=rotulos, ax=ax,
        cmap="Blues", colorbar=False, xticks_rotation=20,
    )
    ax.set_title("Matriz de confusão — árvore de decisão (conjunto de teste)",
                 fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(DIR_MODELO / "matriz_confusao.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    res_dummy.pop("predicao")

    nomes_atributos = melhor.named_steps["pre"].get_feature_names_out().tolist()
    profundidade_grafico = min(3, busca.best_params_["arvore__max_depth"])
    fig, ax = plt.subplots(figsize=(20, 9))
    plot_tree(
        melhor.named_steps["arvore"], max_depth=profundidade_grafico,
        feature_names=nomes_atributos, class_names=melhor.named_steps["arvore"].classes_,
        filled=True, fontsize=7, impurity=False, proportion=True, ax=ax,
    )
    ax.set_title(
        f"Árvore de decisão (primeiros {profundidade_grafico} níveis de "
        f"{busca.best_params_['arvore__max_depth']}) — padrões do modelo, não causas",
        fontsize=12, weight="bold",
    )
    fig.tight_layout()
    fig.savefig(DIR_MODELO / "arvore.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    (DIR_MODELO / "arvore_regras.txt").write_text(
        export_text(melhor.named_steps["arvore"], feature_names=nomes_atributos,
                    max_depth=4, decimals=3),
        encoding="utf-8",
    )

    importancias = (
        pd.DataFrame({
            "atributo": nomes_atributos,
            "importancia": melhor.named_steps["arvore"].feature_importances_,
        })
        .sort_values("importancia", ascending=False)
        .query("importancia > 0")
        .head(25)
    )
    importancias.to_csv(DIR_MODELO / "importancia_atributos.csv", sep=";", index=False,
                        encoding="utf-8-sig")

    # ---- comparacao e relatorios ----
    print("[6/6] Escrevendo metricas...")
    comparacao = pd.DataFrame([
        {"modelo": r["modelo"], "acuracia_global": r["acuracia_global"],
         "acuracia_balanceada": r["acuracia_balanceada"], "macro_f1": r["macro_f1"]}
        for r in (res_arvore, res_dummy)
    ])
    comparacao.to_csv(DIR_MODELO / "comparacao_modelos.csv", sep=";", index=False,
                      encoding="utf-8-sig")

    por_classe = pd.DataFrame([
        {"modelo": r["modelo"], "classe": c, **v}
        for r in (res_arvore, res_dummy) for c, v in r["por_classe"].items()
    ])
    por_classe.to_csv(DIR_MODELO / "metricas_por_classe.csv", sep=";", index=False,
                      encoding="utf-8-sig")

    metricas = {
        "ambiente": ambiente(),
        "arquivo": str(arquivo),
        "sha256_base": hash_arquivo(arquivo),
        "status_da_validacao_antes_do_treino": status_validacao,
        "versao_contrato": contrato["versao_contrato"],
        "configuracao": {
            "semente": SEMENTE,
            "entradas_usadas": entradas,
            "alvo": alvo,
            "class_weight": "balanced" if args.balanceado else None,
            "min_samples_leaf": 50,
            "profundidades_testadas": args.profundidades,
            "max_depth_escolhido": busca.best_params_["arvore__max_depth"],
            "macro_f1_validacao_cruzada_no_treino": round(busca.best_score_, 4),
            "divisao": "80/20 estratificada, feita antes de qualquer transformacao aprendida",
            "onde_o_pipeline_foi_ajustado": "somente no conjunto de treino",
        },
        "dados": {
            "ocorrencias_na_base": int(len(df)),
            "excluidas_por_alvo_ausente": int(excluidas),
            "elegiveis": int(len(elegiveis)),
            "treino": int(len(X_treino)),
            "teste": int(len(X_teste)),
            "suporte_por_classe_total": suporte,
            "suporte_por_classe_treino": y_treino.value_counts().to_dict(),
            "suporte_por_classe_teste": y_teste.value_counts().to_dict(),
            "classes_com_suporte_abaixo_do_minimo": insuficientes,
            "ocorrencias_em_treino_e_teste": len(vazamento_ids),
        },
        "resultados": {"arvore": res_arvore, "referencia": res_dummy},
        "arvore_melhor_que_referencia": {
            "macro_f1": res_arvore["macro_f1"] > res_dummy["macro_f1"],
            "acuracia_balanceada": res_arvore["acuracia_balanceada"] > res_dummy["acuracia_balanceada"],
            "acuracia_global": res_arvore["acuracia_global"] > res_dummy["acuracia_global"],
        },
        "advertencias": [
            "Estudo retrospectivo: avalia acidentes JA REGISTRADOS. Nao e previsao de periodos futuros.",
            "Regras da arvore sao padroes do modelo, nao relacoes causais.",
            "As probabilidades da arvore nao sao risco calibrado, ainda mais com class_weight='balanced'.",
            "Acuracia global e complementar: com 77% de uma classe, um chute fixo ja acerta muito.",
            "Nenhum parametro foi escolhido olhando o conjunto de teste.",
        ],
        "limitacoes": contrato["limitacoes_da_auditoria"],
    }
    salvar_json(metricas, DIR_MODELO / "metricas.json")
    escrever_markdown_modelo(metricas, comparacao, por_classe, importancias,
                             DIR_MODELO / "modelo.md")

    print()
    print("=" * 72)
    print(tabela_markdown(comparacao))
    print()
    print("Metricas por classe:")
    print(por_classe.to_string(index=False))
    print(f"\nRelatorios em {DIR_MODELO}")
    print("=" * 72)
    return 0


def escrever_markdown_modelo(m, comparacao, por_classe, importancias, caminho: Path) -> None:
    c, d = m["configuracao"], m["dados"]
    a, r = m["resultados"]["arvore"], m["resultados"]["referencia"]
    L = ["# Mineracao (complemento de estudo): arvore de decisao\n",
         "> Este resultado e complemento computacional. O trabalho avaliado pede o "
         "PLANEJAMENTO do KDD; nada nos slides depende deste treino.\n",
         f"- Base: `{m['arquivo']}`",
         f"- SHA-256 da base: `{m['sha256_base']}`",
         f"- Status da validacao antes do treino: **{m['status_da_validacao_antes_do_treino']}**",
         f"- Execucao: {m['ambiente']['executado_em']}",
         f"- Versoes: Python {m['ambiente']['python']}, pandas {m['ambiente']['pandas']}, "
         f"scikit-learn {m['ambiente']['scikit_learn']}\n",
         "## Configuracao\n",
         f"- Entradas permitidas (lista explicita do contrato): {c['entradas_usadas']}",
         f"- Alvo: `{c['alvo']}`",
         f"- Divisao: {c['divisao']}",
         f"- Pipeline ajustado: {c['onde_o_pipeline_foi_ajustado']}",
         f"- random_state: {c['semente']}",
         f"- class_weight: {c['class_weight']}",
         f"- min_samples_leaf: {c['min_samples_leaf']}",
         f"- Profundidades testadas por validacao cruzada no treino: {c['profundidades_testadas']}",
         f"- max_depth escolhido: **{c['max_depth_escolhido']}** "
         f"(macro-F1 na CV do treino = {c['macro_f1_validacao_cruzada_no_treino']})\n",
         "## Dados usados\n",
         f"- Ocorrencias na base limpa: {d['ocorrencias_na_base']}",
         f"- Excluidas do treino por alvo ausente: {d['excluidas_por_alvo_ausente']}",
         f"- Elegiveis: {d['elegiveis']} (treino {d['treino']} / teste {d['teste']})",
         f"- Suporte por classe no treino: {d['suporte_por_classe_treino']}",
         f"- Suporte por classe no teste: {d['suporte_por_classe_teste']}",
         f"- Classes com suporte abaixo do minimo: "
         f"{d['classes_com_suporte_abaixo_do_minimo'] or 'nenhuma'}",
         f"- Ocorrencias presentes no treino E no teste: {d['ocorrencias_em_treino_e_teste']} "
         "(precisa ser zero)\n",
         "## Arvore x referencia\n",
         tabela_markdown(comparacao),
         "",
         f"- A arvore superou a referencia em macro-F1? **{m['arvore_melhor_que_referencia']['macro_f1']}**",
         f"- Em acuracia balanceada? **{m['arvore_melhor_que_referencia']['acuracia_balanceada']}**",
         f"- Em acuracia global? **{m['arvore_melhor_que_referencia']['acuracia_global']}**\n",
         "## Metricas por classe\n",
         tabela_markdown(por_classe),
         "",
         "## Matriz de confusao (arvore)\n",
         f"Ordem das classes: {list(a['por_classe'].keys())}\n",
         "```",
         "\n".join(str(linha) for linha in a["matriz_confusao"]),
         "```",
         "\n![Matriz de confusao](matriz_confusao.png)\n",
         "## Arvore aprendida\n",
         "![Arvore de decisao](arvore.png)\n",
         "As regras completas em texto estao em `arvore_regras.txt`. "
         "Elas descrevem o comportamento do MODELO, nao causas de acidente.\n",
         "## Atributos mais usados pela arvore\n",
         tabela_markdown(importancias),
         "",
         "> Importancia alta significa que o atributo foi util para separar as classes "
         "NESTE modelo. Nao significa que ele cause acidentes graves.\n",
         "## Padronizacao de formato x normalizacao de escala\n",
         "- A limpeza padronizou FORMATOS: data `aaaa-mm-dd`, hora `HH:MM:SS`, UF em "
         "maiusculas, categorias com grafia unica.",
         "- NORMALIZAR escala (media 0, desvio 1) e outra operacao, usada por modelos que "
         "comparam magnitudes entre colunas. Arvore de decisao nao precisa: ela testa um "
         "limiar por atributo, de cada vez.\n",
         "## Advertencias\n"]
    L += [f"- {t}" for t in m["advertencias"]]
    L.append("\n## Limitacoes\n")
    L += [f"- {t}" for t in m["limitacoes"]]
    caminho.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
