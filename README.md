# Acidentes da PRF — processo KDD

Trabalho de faculdade aplicando o processo **KDD** (*Knowledge Discovery in
Databases*) sobre a base aberta de acidentes da **Polícia Rodoviária Federal**.

**Pergunta:** quais características temporais, ambientais e estruturais estão
associadas à gravidade dos acidentes registrados em rodovias federais?

A entrega principal é o **planejamento** do KDD (definição do problema, seleção,
pré-processamento, transformação e mineração). O código em `src/` executa essas
etapas de ponta a ponta: diagnóstico, limpeza, validação, análise e — se quiser —
treino de um modelo em comando separado. Não afirmamos causa nem risco por viagem;
trabalhamos com associação observada nos registros.

### Documentação

| arquivo | o que tem |
|---|---|
| [`docs/planejamento_kdd.md`](docs/planejamento_kdd.md) | planejamento completo das etapas |
| [`docs/roteiro_slides.md`](docs/roteiro_slides.md) | o que colocar em cada slide e o que falar |
| [`docs/ficha_tecnica.md`](docs/ficha_tecnica.md) | ficha do trabalho (grupo, ambiente, números) |
| [`reports/`](reports/) | saídas reais das execuções (diagnóstico, limpeza, validação, figuras) |

### Grupo

| nome | função |
|---|---|
| Samuel Souza | código, documentação e roteiro |
| Junior Oliveira | roteiro e organização dos slides |
| Liandra Rodrigues | apresentação e edição dos slides |
| Karolline Oliveira | apresentação |
| Matheus Oliveira | apresentação |

---

## 1. Estrutura do projeto

```
Ciencia de dados/
├─ config/
│  └─ regras_qualidade.json      Contrato de qualidade: domínios, tipos, políticas
│                                 de ausência, regras entre campos e severidades
├─ data/
│  ├─ raw/                       ENTRADA ORIGINAL, preservada e nunca alterada
│  │  ├─ acidentes2025_todas_causas_tipos.csv
│  │  ├─ acidentes2025_todas_causas_tipos.zip
│  │  └─ dicionario_acidentes_prf.pdf
│  ├─ processed/                 Saídas legíveis
│  │  ├─ prf_limpo.csv           BASE PRINCIPAL — uma linha por ocorrência
│  │  ├─ prf_pessoas.csv         Nível pessoa, deduplicado por (id, pesid)
│  │  └─ prf_limpo_esquema.json  Como reabrir o CSV (CSV não guarda tipos)
│  └─ quarantine/
│     ├─ registros_quarentena.csv  Registros com inconsistência crítica + motivo
│     └─ campos_para_revisao.csv   Campos impossíveis, com o valor original
├─ src/
│  ├─ comum.py                   Configuração de leitura, hash, auditoria, utilitários
│  ├─ diagnostico.py             ETAPA 1 — entender antes de mexer
│  ├─ limpeza.py                 ETAPAS 2 e 3 — limpar, agregar, derivar, exportar
│  ├─ validar_dados.py           ETAPA 4 — auditoria independente
│  ├─ exemplo_ficticio.py        ETAPA 5 — tabela Antes × Depois F01–F05
│  ├─ exemplo_real.py            ETAPA 5b — Antes × Depois com ocorrências reais
│  ├─ analise.py                 ETAPA 6 — tabelas e gráficos
│  └─ treinar_modelo.py          ETAPA 7 — treino opcional, comando separado
├─ tests/
│  └─ test_validacao.py          19 testes do validador
├─ tools/
│  └─ corrigir_encoding.py       reconverte fontes para UTF-8
├─ docs/
│  ├─ planejamento_kdd.md        planejamento das etapas
│  ├─ roteiro_slides.md          conteúdo e fala de cada slide
│  └─ ficha_tecnica.md           ficha do trabalho
├─ reports/                      saídas das execuções
├─ requirements.txt
└─ README.md
```

---

## 2. Colocando os arquivos no lugar

A atividade fornece dois arquivos. Coloque-os em `data\raw\`:

| arquivo | nome esperado |
|---|---|
| Base (dentro do ZIP) | `data\raw\acidentes2025_todas_causas_tipos.csv` |
| Dicionário | `data\raw\dicionario_acidentes_prf.pdf` |

Se você tem o ZIP, extraia-o assim (PowerShell, na pasta do projeto):

```powershell
Expand-Archive -Path "data\raw\acidentes2025_todas_causas_tipos.zip" -DestinationPath "data\raw" -Force
```

Confira que o arquivo chegou:

```powershell
Get-ChildItem data\raw | Format-Table Name, Length -AutoSize
```

O CSV tem cerca de 223 MB. Se o nome do seu arquivo for diferente, use
`--entrada "data\raw\SEU_ARQUIVO.csv"` nos comandos das etapas 1 e 2.

---

## 3. Instalação (Windows / PowerShell)

Execute na pasta do projeto. O `.\` antes de `Activate.ps1` é obrigatório.

```powershell
cd "$env:USERPROFILE\Desktop\Ciencia de dados"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação com "execução de scripts foi desabilitada",
libere apenas para a sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Para o terminal exibir acentos corretamente:

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

Confira as versões instaladas:

```powershell
python --version
python -c "import pandas, sklearn, matplotlib, seaborn; print(pandas.__version__, sklearn.__version__, matplotlib.__version__, seaborn.__version__)"
```

---

## 4. Executando o projeto, etapa por etapa

Cada comando é independente e pode ser repetido. Rode-os na ordem na primeira vez.

### Etapa 1 — Diagnóstico (antes de limpar)

```powershell
python src\diagnostico.py
```

Lê o arquivo bruto em blocos, **sem corrigir nada**, com todas as colunas como
texto. Responde: quantas linhas e colunas, quais tipos, ausências por coluna,
categorias e frequências, duplicatas exatas, conflitos de chave, erros de conversão,
intervalo de datas e qual é a unidade de cada linha.

Gera: `reports/diagnostico.md`, `diagnostico.json`, `diagnostico_colunas.csv`,
`diagnostico_categorias.csv`.

Opções:

```powershell
python src\diagnostico.py --entrada "data\raw\outro_arquivo.csv" --bloco 100000
```

### Etapa 2 — Limpeza, agregação e transformação

```powershell
python src\limpeza.py
```

Executa 11 passos documentados: leitura controlada, cabeçalhos, limpeza de texto,
tokens de ausência por coluna, mapas explícitos de categoria, revisão de campos
impossíveis, verificação de integridade da chave, **agregação para a unidade
ocorrência**, atributos derivados, sinalização de elegibilidade e exportação.

Gera: `data/processed/prf_limpo.csv`, `prf_pessoas.csv`,
`prf_limpo_esquema.json`, `data/quarantine/*.csv`,
`reports/limpeza.md`, `limpeza.json`, `auditoria_limpeza.csv`,
`limpeza_antes_depois.csv`, `reconciliacao.csv`, `composicao_classes.csv`,
`mapa_tracado_via.csv`.

Opções:

```powershell
# teste rápido com as primeiras 50 mil linhas
python src\limpeza.py --amostra 50000

# gravar em pasta isolada, sem tocar nos arquivos reais
python src\limpeza.py --amostra 50000 --base-saida "tests\tmp\experimento"
```

### Etapa 3 — Validação independente do CSV salvo

```powershell
python src\validar_dados.py
```

Reabre `data/processed/prf_limpo.csv` como **texto puro** e aplica o contrato de
qualidade **sem limpar, preencher ou corrigir nada**. Para cada regra informa
identificador, descrição, severidade, status, linhas avaliadas, quantidade e
percentual de violações e exemplos rastreáveis.

Gera: `reports/validacao.md`, `validacao.json`, `validacao_regras.csv`,
`qualidade_antes_depois.csv`.

Validar outro arquivo:

```powershell
python src\validar_dados.py --arquivo "data\processed\prf_limpo.csv"
python src\validar_dados.py --arquivo "meu_arquivo.csv" --sem-reconciliacao
```

Ver o código de saída da última execução:

```powershell
python src\validar_dados.py
echo "codigo de saida: $LASTEXITCODE"
```

### Etapa 4 — Testes do próprio validador

```powershell
python tests\test_validacao.py
```

Ou, com pytest:

```powershell
pip install pytest
python -m pytest tests -v
```

Cria arquivos sintéticos isolados dos dados reais, cada um com um defeito conhecido
(coluna ausente, chave conflitante, data 30 de fevereiro, categoria inexistente,
contagem negativa, índice exportado, alvo ausente) e confirma que o validador
reprova pelo motivo certo. Também prova que **limpar duas vezes gera exatamente o
mesmo arquivo**, byte a byte, na mesma ordem.

### Etapa 5 — Tabela Antes × Depois para o slide

```powershell
python src\exemplo_ficticio.py
```

Gera: `reports/exemplo_antes.csv`, `exemplo_depois.csv`, `exemplo_antes.png`,
`exemplo_antes_depois.png`, `exemplo_codificacao.csv`, `exemplo_codificacao.png`,
`exemplo_ficticio.md`.

Os cinco registros são **fictícios** (F01–F05), levam o aviso
"Exemplo fictício — não representa resultados da PRF" e não entram em nenhum gráfico
real, treinamento ou métrica.

### Etapa 5b — Recortes Antes × Depois com dados reais

```powershell
python src\exemplo_real.py
```

Gera: `reports/exemplo_real_agregacao_antes.png` e `_depois.png`,
`exemplo_real_antes.png`, `exemplo_real_depois.png`, `exemplo_real_mudancas.png`,
`exemplo_real_derivados.png`, os CSVs equivalentes e `exemplo_real.md`.

Complementa a etapa anterior com linhas **reais**, rastreáveis pelo `id` da
ocorrência: dá para abrir o arquivo bruto e a base limpa durante a apresentação e
conferir célula por célula. São dois recortes:

- **Agregação:** uma ocorrência que ocupa 8 linhas no arquivo bruto. Somar a coluna
  `mortos` linha a linha dá 8 mortos; a ocorrência teve 1 vítima fatal. É a evidência
  concreta de por que a base foi agregada para a unidade ocorrência.
- **Padronização:** cinco ocorrências, cada uma com um problema diferente (token
  `Ignorado`, `tracado_via` fora de ordem, `uso_solo` como `Sim`/`Não`, `dia_semana`
  em minúsculas, `sentido_via` não informado), mais a tabela que lista só as células
  alteradas e a regra responsável por cada uma.

A escolha das ocorrências é **determinística**: os mesmos arquivos de entrada geram
sempre os mesmos exemplos. Nada é sorteado.

### Etapa 6 — Análise descritiva

```powershell
python src\analise.py
```

Revalida a base antes de qualquer gráfico. **Se uma regra crítica falhar, a análise é
bloqueada.** Gera tabelas e gráficos com o denominador sempre visível e marcação de
grupos pequenos.

Gera: `reports/analise.md`, `analise.json`, `tabela_*.csv`, `reports/figuras/*.png`
(incluindo as variantes de visual `09` a `19`: pizza, rosca, barras horizontais,
barras agrupadas, heatmap e pizzas comparativas).

Opções:

```powershell
python src\analise.py --minimo-grupo 100
python src\analise.py --pular-validacao     # não recomendado
```

### Etapa 7 — Treino do modelo (opcional)

O treino fica em comando separado de propósito: os slides não dependem dele.

```powershell
python src\treinar_modelo.py
```

Variante com pesos de classe balanceados (grava em pasta própria):

```powershell
python src\treinar_modelo.py --balanceado
```

Outras opções:

```powershell
python src\treinar_modelo.py --profundidades 3 4 5 6 8 10 12
python src\treinar_modelo.py --minimo-por-classe 100
```

Gera: `reports/modelo/modelo.md`, `metricas.json`, `matriz_confusao.png`,
`arvore.png`, `arvore_regras.txt`, `comparacao_modelos.csv`,
`metricas_por_classe.csv`, `importancia_atributos.csv`. Com `--balanceado`, o mesmo
conjunto em `reports/modelo_balanceado/`.

### Rodar tudo de uma vez

```powershell
python src\diagnostico.py; `
python src\limpeza.py; `
python src\validar_dados.py; `
python tests\test_validacao.py; `
python src\exemplo_ficticio.py; `
python src\exemplo_real.py; `
python src\analise.py; `
python src\treinar_modelo.py; `
python src\treinar_modelo.py --balanceado
```

---

## 5. Códigos de saída

Todos os scripts seguem a mesma convenção. Consulte com `$LASTEXITCODE`.

| código | significado | o que fazer |
|---|---|---|
| `0` | Sucesso. Para o validador: **APROVADA** ou **APROVADA_COM_RESSALVAS** (as ressalvas ficam documentadas em `reports/validacao.md`) | seguir para a próxima etapa |
| `1` | Falha de qualidade: uma regra **crítica** falhou ou não pôde ser verificada | abrir `reports/validacao.md`, seção "Evidências das regras que não passaram", corrigir a causa e rodar de novo |
| `2` | Erro operacional: arquivo ausente, arquivo vazio, ilegível, contrato não encontrado | conferir se o arquivo está em `data\raw\` e se `config\regras_qualidade.json` existe |

Uma regra crítica que falha **ou** que não pôde ser verificada impede a aprovação.
`analise.py` e `treinar_modelo.py` se bloqueiam sozinhos quando o validador devolve
código diferente de 0.

---

## 6. Como revisar a quarentena

Existem dois arquivos, com propósitos diferentes.

### `data/quarantine/registros_quarentena.csv` — registro inteiro retido

Recebe a linha completa quando a ocorrência tem **inconsistência crítica de chave**:
colunas que deveriam descrever a ocorrência (data, UF, gravidade, pista...) aparecem
com valores diferentes dentro do mesmo `id`. Nesse caso a ocorrência inteira não vai
para a base, porque agregá-la exigiria escolher arbitrariamente um dos valores.

```powershell
Import-Csv "data\quarantine\registros_quarentena.csv" -Delimiter ';' | Measure-Object | Select-Object Count
Import-Csv "data\quarantine\registros_quarentena.csv" -Delimiter ';' | Select-Object -First 5 motivo_quarentena, id, data_inversa, uf
```

### `data/quarantine/campos_para_revisao.csv` — campo suspeito, registro mantido

Recebe uma cópia rastreável quando **um campo** tem valor impossível, mas o registro
continua útil. Hoje a regra ativa é `idade` fora de 0–120 anos. O valor impossível
vira ausência na base limpa, e o valor original fica preservado aqui e na auditoria.

```powershell
Import-Csv "data\quarantine\campos_para_revisao.csv" -Delimiter ';' | Group-Object motivo | Select-Object Count, Name
Import-Csv "data\quarantine\campos_para_revisao.csv" -Delimiter ';' | Select-Object -First 10 id, pesid, coluna, valor_original, motivo, acao
```

### Rastrear uma alteração específica na auditoria

`reports/auditoria_limpeza.csv` guarda arquivo de origem, linha, `id`, coluna, regra
aplicada, valor anterior e valor posterior.

```powershell
Import-Csv "reports\auditoria_limpeza.csv" -Delimiter ';' | Where-Object { $_.id_origem -eq '652468' } | Format-Table -AutoSize
Import-Csv "reports\auditoria_limpeza.csv" -Delimiter ';' | Group-Object regra | Sort-Object Count -Descending | Select-Object Count, Name
```

Para regras que afetam centenas de milhares de células (mapeamento de `dia_semana`,
`uso_solo`, tokens de ausência, reordenação de `tracado_via`), a auditoria grava uma
**amostra rastreável por regra**, com limite fixo no código. As contagens completas
estão em `reports/limpeza.json`, nos campos `passos.3_texto`,
`passos.4_tokens_ausencia` e `passos.5_categorias`.

---

## 7. Como abrir a base limpa

O CSV **não guarda tipos**. Sempre consulte `data/processed/prf_limpo_esquema.json`.

No Excel: o arquivo está em UTF-8 com BOM e separador `;`, então abre com acentos
corretos por duplo clique.

Em Python, leia como texto e converta depois:

```python
import pandas as pd

df = pd.read_csv(
    "data/processed/prf_limpo.csv",
    sep=";", encoding="utf-8-sig", dtype=str,
)
df["data_inversa"] = pd.to_datetime(df["data_inversa"], format="%Y-%m-%d")
df["km"] = pd.to_numeric(df["km"].str.replace(",", "."), errors="coerce")
df["qtd_mortos"] = pd.to_numeric(df["qtd_mortos"])
```

---

## 8. Onde encontrar cada resposta

| pergunta | arquivo |
|---|---|
| Como é o arquivo bruto e o que há de errado nele? | `reports/diagnostico.md` |
| O que foi corrigido e quantas linhas foram para onde? | `reports/limpeza.md`, `reports/reconciliacao.csv` |
| A base limpa passou nas regras? | `reports/validacao.md` |
| Quais regras existem e de onde vêm? | `config/regras_qualidade.json` |
| Antes × Depois para o slide (exemplo didático) | `reports/exemplo_ficticio.md`, `reports/exemplo_antes_depois.png` |
| Antes × Depois com dados reais e `id` rastreável | `reports/exemplo_real.md`, `reports/exemplo_real_mudancas.png` |
| Distribuição e composição da gravidade | `reports/analise.md`, `reports/figuras/` |
| Resultado do modelo | `reports/modelo/modelo.md`, `reports/modelo_balanceado/modelo.md` |
| Planejamento conceitual do KDD | `docs/planejamento_kdd.md` |
| Roteiro dos slides | `docs/roteiro_slides.md` |
| Ficha técnica | `docs/ficha_tecnica.md` |

---

## 9. Solução de problemas

**`ModuleNotFoundError: No module named 'comum'`** — rode os scripts pela raiz do
projeto, como nos comandos acima (`python src\limpeza.py`), não de dentro de `src`.

**`UnicodeDecodeError` ao ler o arquivo bruto** — o arquivo da PRF é `latin-1`, não
UTF-8. A configuração já está em `src/comum.py`, campo `LEITURA_BRUTO`. Se você
trocou o arquivo por outra versão, confirme a codificação antes.

**Acentos aparecendo como `?` no terminal** — é só o console do Windows. Rode
`chcp 65001` (seção 3). Os arquivos gravados estão corretos.

**`MemoryError` no diagnóstico** — reduza o bloco: `--bloco 50000`.

**`SyntaxWarning: invalid escape sequence`** — cosmético, vindo de caminhos do
Windows em textos de ajuda. Não afeta o resultado.

**Fontes com acento quebrado depois de editar** — rode
`python tools\corrigir_encoding.py` para reconverter tudo para UTF-8.

---

## 10. Fontes

- [Dados abertos da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf)
- [Dicionários de dados da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes)
- [Fayyad, Piatetsky-Shapiro e Smyth — KDD, 1996](https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/view/1230)
- [pandas: leitura de CSV](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [scikit-learn: prevenção de vazamento de dados](https://scikit-learn.org/stable/common_pitfalls.html)
- [scikit-learn: árvore de decisão](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html)
- [scikit-learn: métricas de classificação](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
