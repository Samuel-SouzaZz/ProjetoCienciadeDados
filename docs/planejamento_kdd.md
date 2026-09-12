# Planejamento KDD — Gravidade dos acidentes em rodovias federais (PRF)

> Documento conceitual do trabalho. As etapas do KDD adotadas são **definição do
> problema, seleção, pré-processamento, transformação e mineração**. A etapa de
> interpretação não faz parte da entrega exigida.
>
> Todos os números citados aqui vêm de execuções reais registradas em `reports/`.
> Nada foi estimado de cabeça.

---

## 1. Definição do problema

**Pergunta:** quais características temporais, ambientais e estruturais estão
associadas à gravidade dos acidentes registrados em rodovias federais?

**Unidade de análise:** uma ocorrência de acidente (um valor de `id`).

**Tarefa de mineração:** classificação da gravidade, usando `classificacao_acidente`
como variável-alvo, com as categorias confirmadas no dicionário da PRF.

### O que esta análise NÃO permite

Estes limites não são detalhe: são parte da resposta correta.

1. **Não estima a probabilidade de uma viagem sofrer acidente.** A base contém
   apenas acidentes que aconteceram e foram registrados. Não existe informação de
   quantas viagens ocorreram sem acidente.
2. **Não mede risco.** Frequência bruta não é risco sem dados de exposição ao
   trânsito (volume de veículos, quilômetros rodados, tempo de exposição). Se a
   maioria dos acidentes acontece com "Céu Claro", isso pode significar apenas que
   a maioria das viagens acontece com céu claro.
3. **Não prova causa.** Associação observada em registros não é relação causal.
4. **Não prevê o futuro.** A avaliação treino/teste é retrospectiva: mede se o
   modelo consegue separar registros que já existem.
5. **Depende do registro policial.** A base descreve o que o policial anotou no
   Boletim de Acidente de Trânsito, não a realidade completa do evento.

---

## 2. Seleção — a base e o dicionário

| item | valor confirmado |
|---|---|
| Arquivo | `acidentes2025_todas_causas_tipos.csv` (extraído do ZIP fornecido) |
| Tamanho | 223.019.483 bytes |
| Dicionário | `dicionario_acidentes_prf.pdf` (5 páginas, 37 variáveis) |
| Linhas | 584.010 |
| Colunas | 37 |
| Separador | `;` |
| Codificação | `latin-1` (o byte `0xE7`, de "ç", quebra a leitura em UTF-8) |
| Decimal | vírgula (`km = 89,5`, `latitude = -8,20760697`) |
| Texto | entre aspas duplas |
| Tokens de ausência | `NA`, `(null)`, além de tokens textuais por coluna |
| Período real | 2025-01-01 a 2025-12-31 |
| Formato de data no arquivo | `aaaa-mm-dd` em 584.010 de 584.010 linhas |

### Descoberta mais importante da seleção: a unidade da linha

O dicionário diz, na capa, que os dados são **agregados por pessoa, com todas as
causas e tipos de acidentes**. O diagnóstico confirmou:

| medida | valor |
|---|---|
| Linhas do arquivo | 584.010 |
| `id` de acidente distintos | 72.529 |
| Pares (`id`, `pesid`) distintos | 188.346 |
| Combinações (`id`, `pesid`, causa, ordem do tipo) distintas | 560.828 |
| Média de linhas por ocorrência | 8,05 |

**Consequência prática:** `id` repetido **não é duplicata**. Cada pessoa envolvida
aparece uma vez para cada combinação de causa e tipo de acidente. Somar colunas
diretamente multiplica as vítimas. A prova numérica:

| medida | somando todas as linhas | somando por (`id`, `pesid`) distinto | fator de inflação |
|---|---|---|---|
| mortos | 27.912 | 6.043 | 4,6× |
| feridos leves | 179.140 | 63.532 | 2,8× |
| feridos graves | 66.983 | 20.018 | 3,3× |
| ilesos | 218.091 | 76.406 | 2,9× |

Por isso o projeto **agrega por `id`** para chegar à unidade desejada, e faz todas
as contagens de vítimas sobre pares (`id`, `pesid`) distintos.

### A agregação é segura? Sim, e isso foi verificado

Antes de agregar, o script conferiu se as 19 colunas que descrevem a ocorrência
(data, hora, UF, gravidade, pista, traçado, clima etc.) são constantes dentro de
cada `id`. Resultado: **0 dos 72.529 `id` apresentaram conflito**. Se houvesse
conflito, a ocorrência iria para quarentena em vez de para a base.

### Divergências entre dicionário e arquivo

| dicionário | arquivo | tratamento |
|---|---|---|
| `classificação_acidente` (com cedilha e acento) | `classificacao_acidente` | mapa de cabeçalhos documentado |
| `condição_meteorologica` | `condicao_metereologica` (grafia com erro na origem) | mantida a grafia real do arquivo, com mapa |
| `data_inversa` no formato `dd/mm/aaaa` | `aaaa-mm-dd` em 100% das linhas | adotado `aaaa-mm-dd` como formato canônico |
| `km` com mínimo de 0,1 | existem valores 0 | valores preservados e apenas sinalizados como aviso |
| `idade` com código `-1` para ausência | nenhum `-1` encontrado | nada a converter |

Nenhuma variável do dicionário está ausente do arquivo, e nenhuma coluna do
arquivo está fora do dicionário: **37 de 37**.

---

## 3. Seleção dos atributos — todas as 37 colunas

Legenda de decisão: **ENTRADA** = entra em X; **ALVO** = variável-alvo;
**FORA (vazamento)** = revelaria a resposta; **FORA (metadado)** = identificador ou
dado administrativo; **FORA (apuração)** = informação apurada sobre a ocorrência,
não condição prévia; **AGREGADO** = usada para construir uma coluna derivada.

> "Descartar da análise" significa **excluir da seleção do modelo**. Nenhum dado de
> origem foi destruído: `data/raw/` está intacto e `prf_pessoas.csv` preserva o
> nível pessoa.

| # | coluna | nível | significado (dicionário) | papel | decisão | justificativa |
|---|---|---|---|---|---|---|
| 1 | `id` | ocorrência | identificador do acidente | identificador | FORA (metadado) | é chave de rastreabilidade; usar como entrada faria o modelo "decorar" registros |
| 2 | `pesid` | pessoa | identificador da pessoa envolvida | identificador | AGREGADO | usado para contar pessoas distintas sem duplicar |
| 3 | `data_inversa` | ocorrência | data da ocorrência | temporal | AGREGADO / FORA de X | usada para recorte e para derivar mês, dia da semana e fim de semana; a data exata em si não é condição generalizável |
| 4 | `dia_semana` | ocorrência | dia da semana | temporal | **ENTRADA** | condição temporal explicitamente pedida pela pergunta |
| 5 | `horario` | ocorrência | horário da ocorrência | temporal | AGREGADO / FORA de X | usado para derivar `hora` e `faixa_horaria`; 86.400 valores distintos não generalizam |
| 6 | `uf` | ocorrência | Unidade da Federação | recorte | FORA (recorte) | serve a recorte e contexto; entraria como proxy geográfica, deslocando o foco das condições da via |
| 7 | `br` | ocorrência | identificador da BR | contexto | FORA (metadado) | identificação de trecho, não condição ambiental; ausente em 1.444 linhas |
| 8 | `km` | ocorrência | quilômetro da ocorrência | contexto | FORA (metadado) | localização pontual; não generaliza |
| 9 | `municipio` | ocorrência | município da ocorrência | contexto | FORA (metadado) | alta cardinalidade e natureza geográfica |
| 10 | `causa_principal` | causa | indica se a causa foi a principal | apuração | AGREGADO | usado para escolher a causa principal registrada |
| 11 | `causa_acidente` | causa | causa presumível do acidente | apuração | FORA (apuração) | é conclusão do policial **após** o acidente; incluir desloca a pergunta de "condições" para "apuração", e algumas causas quase descrevem o desfecho |
| 12 | `ordem_tipo_acidente` | tipo | sequência dos eventos | apuração | AGREGADO | usado para identificar o primeiro tipo (ordem 1) |
| 13 | `tipo_acidente` | tipo | tipo do acidente | apuração | FORA (apuração) | mesma razão de `causa_acidente`: descreve a dinâmica já ocorrida (ex.: "Atropelamento de Pedestre" antecipa gravidade) |
| 14 | `classificacao_acidente` | ocorrência | gravidade: Sem Vítimas, Com Vítimas Feridas, Com Vítimas Fatais, Ignorado | **ALVO** | **ALVO** | é exatamente a gravidade que a pergunta investiga |
| 15 | `fase_dia` | ocorrência | fase do dia (Amanhecer, Pleno dia...) | temporal/ambiental | **ENTRADA** | condição de luminosidade no momento do acidente |
| 16 | `sentido_via` | ocorrência | sentido crescente/decrescente | contexto | FORA (metadado) | referência de sentido do trecho, sem significado ambiental próprio; ausente em 1.444 linhas |
| 17 | `condicao_metereologica` | ocorrência | condição meteorológica | ambiental | **ENTRADA** | condição ambiental explicitamente pedida |
| 18 | `tipo_pista` | ocorrência | Simples, Dupla ou Múltipla | estrutural | **ENTRADA** | característica estrutural da via |
| 19 | `tracado_via` | ocorrência | descrição do traçado | estrutural | **ENTRADA** | característica estrutural da via (reta, curva, aclive, ponte...) |
| 20 | `uso_solo` | ocorrência | Urbano=Sim; Rural=Não | estrutural | **ENTRADA** | característica do local |
| 21 | `id_veiculo` | veículo | identificador do veículo | identificador | AGREGADO | usado para contar veículos distintos |
| 22 | `tipo_veiculo` | veículo | tipo do veículo (Art. 96 CTB) | apuração | FORA (apuração) | descreve os envolvidos, não a condição da via; múltiplos veículos por ocorrência exigiriam decisão extra |
| 23 | `marca` | veículo | marca do veículo | apuração | FORA (apuração) | 7.527 valores distintos; irrelevante para a pergunta; usa `NA/NA` como ausência disfarçada |
| 24 | `ano_fabricacao_veiculo` | veículo | ano de fabricação | apuração | FORA (apuração) | característica do veículo; 29.808 linhas com `0` (ausência disfarçada) |
| 25 | `tipo_envolvido` | pessoa | condutor, passageiro, pedestre... | apuração | FORA (apuração) | nível pessoa; "Pedestre" antecipa o tipo e a gravidade |
| 26 | `estado_fisico` | pessoa | morto, ferido leve... | **desfecho** | FORA (vazamento) | é o desfecho da pessoa: entrega a resposta ao algoritmo |
| 27 | `idade` | pessoa | idade do envolvido | apuração | FORA (apuração) | nível pessoa; 432 valores impossíveis (até 2024) tratados na revisão de campos |
| 28 | `sexo` | pessoa | sexo do envolvido | apuração | FORA (apuração) | nível pessoa; não é condição temporal, ambiental ou estrutural |
| 29 | `ilesos` | pessoa | binário: envolvido ileso | **desfecho** | FORA (vazamento) → `qtd_ilesos` | mede o resultado do acidente |
| 30 | `feridos_leves` | pessoa | binário: ferido leve | **desfecho** | FORA (vazamento) → `qtd_feridos_leves` | mede o resultado |
| 31 | `feridos_graves` | pessoa | binário: ferido grave | **desfecho** | FORA (vazamento) → `qtd_feridos_graves` | mede o resultado |
| 32 | `mortos` | pessoa | binário: morto | **desfecho** | FORA (vazamento) → `qtd_mortos` | determina diretamente "Com Vítimas Fatais" |
| 33 | `latitude` | ocorrência | latitude decimal | contexto | FORA (metadado) | coordenada de rastreabilidade e mapa |
| 34 | `longitude` | ocorrência | longitude decimal | contexto | FORA (metadado) | idem |
| 35 | `regional` | ocorrência | superintendência regional da PRF | metadado | FORA (metadado) | divisão administrativa; o dicionário avisa que nem coincide com a UF do acidente |
| 36 | `delegacia` | ocorrência | delegacia da PRF | metadado | FORA (metadado) | divisão administrativa |
| 37 | `uop` | ocorrência | unidade operacional da PRF | metadado | FORA (metadado) | divisão administrativa |

**Atributos do dicionário ausentes no arquivo:** nenhum.
**Colunas do arquivo fora do dicionário:** nenhuma.

### Atributos derivados criados por este projeto

| coluna | origem | papel | entra em X? |
|---|---|---|---|
| `ano`, `mes`, `mes_nome` | `data_inversa` | temporal | apenas `mes` |
| `hora` | `horario` | temporal | não (usada para derivar a faixa) |
| `faixa_horaria` | `hora` | temporal | **sim** |
| `fim_de_semana` | dia da semana calculado | temporal | **sim** |
| `dia_semana_calculado`, `dia_semana_divergente` | `data_inversa` | controle de qualidade | não |
| `qtd_pessoas`, `qtd_ilesos`, `qtd_feridos_leves`, `qtd_feridos_graves`, `qtd_feridos`, `qtd_mortos`, `qtd_estado_fisico_nao_informado` | nível pessoa, deduplicado | desfecho | **não — vazamento** |
| `qtd_veiculos`, `qtd_causas_distintas`, `qtd_tipos_distintos` | agregação | apuração | não |
| `causa_principal_acidente`, `tipo_acidente_principal` | agregação | apuração | não |
| `alvo_ausente`, `elegivel_modelo`, `motivo_inelegibilidade` | controle | sinalizador | não |
| `entradas_ausentes` | controle | sinalizador informativo | não |

### Lista explícita de entradas permitidas (X)

Nada entra em X "por exclusão". A lista fica no contrato
(`config/regras_qualidade.json`, campo `entradas_modelo_permitidas`):

```
dia_semana, faixa_horaria, fim_de_semana, mes,
fase_dia, condicao_metereologica, tipo_pista, tracado_via, uso_solo
```

São 9 atributos: 4 temporais, 2 ambientais e 3 estruturais. Exatamente o escopo da
pergunta.

---

## 4. Pré-processamento — o que estava errado e o que foi feito

Todos os problemas abaixo foram **encontrados na execução**, não presumidos.

### 4.1 Problemas encontrados

| # | problema | evidência | severidade |
|---|---|---|---|
| P1 | A linha não é uma ocorrência: são 8,05 linhas por acidente | 584.010 linhas / 72.529 `id` | crítico (invalida a análise por ocorrência) |
| P2 | Somar vítimas direto infla os números | 27.912 mortos vs 6.043 reais | crítico |
| P3 | `tracado_via` é multivalorado com `;` e **sem ordem fixa** | 605 rótulos brutos para 12 componentes atômicos | alto |
| P4 | Codificação não é UTF-8 | byte `0xE7` inválido em UTF-8 | crítico (texto ilegível se ignorado) |
| P5 | Ausência disfarçada de categoria | `Ignorado` em clima (7.130), `Não Informado` em sentido (1.444) e estado físico (35.083), `NA/NA` em marca (18.617), `0` em ano de fabricação (29.808) | alto |
| P6 | `idade` impossível | 432 linhas com idade acima de 120 (valores como 1924, 2024) | alto |
| P7 | Capitalização inconsistente | `sábado` minúsculo; `Pleno dia` ao lado de `Plena Noite` | médio |
| P8 | Rótulo pouco legível | `uso_solo` como Sim/Não, quando o dicionário diz Urbano/Rural | médio |
| P9 | `km` abaixo do mínimo do dicionário | 1.253 linhas brutas com `km = 0`, sendo o mínimo declarado 0,1 | aviso |
| P10 | Alvo ausente | 7 linhas brutas, correspondendo a **1 ocorrência** (`id` 652519) | crítico para o treino |
| P11 | Espaços e caracteres invisíveis | 201 células corrigidas | baixo |
| P12 | Ocorrências sem veículo identificado | 5 ocorrências | aviso |

### 4.2 O que NÃO era problema (verificado, não suposto)

- **Duplicatas exatas: 0.** Nenhuma linha idêntica a outra.
- **Erros de formato: 0.** Todas as datas em `aaaa-mm-dd`, horários em `HH:MM:SS`,
  inteiros sem parte fracionária, decimais com vírgula.
- **Conflitos de chave: 0.** Colunas da ocorrência constantes dentro de cada `id`.
- **`dia_semana` divergente da data: 0** entre as 72.529 ocorrências.
- **Coerência gravidade × contagens: perfeita.** Nenhuma ocorrência "Sem Vítimas"
  com ferido ou morto; todas as "Com Vítimas Fatais" têm morto; todas as "Com
  Vítimas Feridas" têm ferido e nenhum morto.

### 4.3 Correções aplicadas

| passo | ação | volume |
|---|---|---|
| 1 | Leitura com `sep=';'`, `encoding='latin-1'`, `decimal=','`, tudo como texto | 584.010 linhas, 0 ilegíveis |
| 2 | Mapa de cabeçalhos original → padronizado, sem colisão | 37 colunas, 0 renomeadas |
| 3 | Remoção de espaços duplicados e caracteres invisíveis | 201 células |
| 4 | Tokens de ausência **por coluna** (nunca global) | 128.336 células |
| 5 | Mapas explícitos de categoria; UF em maiúsculas | `dia_semana` 584.010; `uso_solo` 584.010; `fase_dia` 324.063 |
| 5b | Ordenação alfabética dos componentes de `tracado_via` | 108.266 células; 605 → 230 rótulos |
| 6 | `idade` fora de 0–120 vira ausência, com o original preservado | 432 registros em `data/quarantine/campos_para_revisao.csv` |
| 7 | Verificação de integridade da chave antes de agregar | 0 conflitos |
| 8 | Agregação para ocorrência, contando pares distintos | 584.010 → 72.529 |
| 9 | Derivação de mês, hora, faixa horária, fim de semana, dia da semana recalculado | 0 falhas de conversão |
| 10 | Sinalização de alvo ausente e elegibilidade | 1 ocorrência inelegível |
| 11 | Exportação com auditoria e reconciliação | 20.633 registros de auditoria |

### 4.4 Políticas de ausência

**Proibido neste projeto:**
- `fillna(0)` global;
- imputar `classificacao_acidente`, `qtd_mortos` ou qualquer contagem de vítimas
  por média, moda ou chute;
- remover uma linha só porque ela contém alguma ausência.

**Adotado:**
- cada coluna tem sua própria política, declarada no contrato;
- alvo ausente **permanece na base limpa** com `alvo_ausente = Sim` e
  `elegivel_modelo = Não`, e fica fora do treino supervisionado com o motivo
  contado;
- ausência em atributo de **entrada** vira a categoria explícita `(ausente)` dentro
  do Pipeline, ajustado só no treino. Isso preserva a informação "não foi
  informado" em vez de fingir que era o valor mais comum;
- a coluna `entradas_ausentes` registra, de forma apenas informativa, quais entradas
  faltam em cada ocorrência. Ela é separada de `motivo_inelegibilidade` de propósito:
  ausência em entrada **não** torna o registro inelegível, e misturar as duas coisas
  daria a impressão errada. A regra crítica R16 do contrato impede essa mistura.

### 4.5 Reconciliação das linhas

Todas as linhas de entrada terminam em destinos mutuamente exclusivos:

| destino | linhas |
|---|---|
| Entrada | 584.010 |
| Duplicatas exatas removidas | 0 |
| Enviadas à quarentena | 0 |
| Mantidas e agregadas | 584.010 |
| **Soma dos destinos** | **584.010 ✔** |

Resultado: 72.529 ocorrências e 177.479 pessoas distintas.

### 4.6 As exclusões mudaram a composição das classes?

Praticamente não, porque só 1 ocorrência foi excluída do treino.

| gravidade | base limpa | % | elegíveis | % |
|---|---|---|---|---|
| Com Vítimas Feridas | 56.181 | 77,460 | 56.181 | 77,461 |
| Sem Vítimas | 11.138 | 15,357 | 11.138 | 15,357 |
| Com Vítimas Fatais | 5.209 | 7,182 | 5.209 | 7,182 |
| (ausente) | 1 | 0,001 | 0 | 0,000 |

---

## 5. Transformação

### Atributos derivados e seus limites

| atributo | regra |
|---|---|
| `mes` | mês de `data_inversa` |
| `fim_de_semana` | `Sim` quando o dia da semana **calculado** é Sábado ou Domingo |
| `faixa_horaria` | Madrugada 00:00:00–05:59:59; Manhã 06:00:00–11:59:59; Tarde 12:00:00–17:59:59; Noite 18:00:00–23:59:59 |

> **`faixa_horaria` não é `fase_dia`.** A faixa é uma divisão do relógio criada por
> este projeto. `fase_dia` é a fase de luz que o policial registrou (Amanhecer,
> Pleno Dia, Anoitecer, Plena Noite). Um acidente às 18:30 pode ser "Noite" pelo
> relógio e "Anoitecer" pelo registro da PRF, ao mesmo tempo.

### Padronização de formato ≠ normalização numérica

- **Padronizar formato** é deixar a data como `aaaa-mm-dd`, a hora como `HH:MM:SS`,
  a UF em maiúsculas e cada categoria com uma grafia única. É o que a limpeza fez.
- **Normalizar escala** é transformar números para média 0 e desvio 1 (ou para o
  intervalo 0–1). Serve a modelos que comparam magnitudes entre colunas. **Árvore de
  decisão não precisa disso**, porque testa um limiar por atributo, separadamente.

### Três objetos diferentes

1. **Base legível** (`data/processed/prf_limpo.csv`): rótulos em português, para
   humano ler, conferir e abrir no Excel.
2. **X transformado**: matriz numérica produzida pelo `OneHotEncoder` dentro do
   Pipeline, ajustada **somente no treino**. Não é arquivo de leitura humana.
3. **y**: apenas a coluna `classificacao_acidente` das linhas elegíveis.

A tabela fictícia F01–F05 (`reports/exemplo_ficticio.md`) mostra visualmente o
antes/depois e um recorte da codificação. Esses cinco registros **não** entram em
gráfico, treino nem métrica.

---

## 6. Mineração proposta

**Técnica:** árvore de decisão de classificação (`DecisionTreeClassifier`).

**Justificativa:** a tarefa é categórica (três classes de gravidade) e a árvore
permite **ler** as regras aprendidas, o que é essencial em trabalho didático. A
profundidade é limitada para o modelo não decorar a base.

**Protocolo, para não haver vazamento:**

1. Divisão 80/20 **estratificada**, feita **antes** de qualquer transformação
   aprendida, com `random_state=42`.
2. Verificação de que a mesma ocorrência não está nos dois conjuntos.
3. `Pipeline` + `ColumnTransformer` com `SimpleImputer` e
   `OneHotEncoder(handle_unknown="ignore")`, ajustados **só no treino**.
4. `max_depth` escolhido por validação cruzada estratificada de 5 partes **dentro
   do treino**. O conjunto de teste não participa de nenhuma escolha.
5. Comparação obrigatória com `DummyClassifier(strategy="most_frequent")`.

**Métricas:** matriz de confusão, precisão/recall/F1 por classe com suporte,
macro-F1 e acurácia balanceada. Acurácia global é apenas complementar: como 77,46%
das ocorrências são "Com Vítimas Feridas", chutar sempre essa classe já acerta
77,46%.

### Resultado real da execução complementar

Duas execuções foram feitas. Os dois resultados são reportados, inclusive o ruim.

| execução | acurácia global | acurácia balanceada | macro-F1 |
|---|---|---|---|
| Árvore, sem `class_weight` (`max_depth=5`) | 0,7746 | 0,3333 | 0,2910 |
| **Referência** `DummyClassifier(most_frequent)` | 0,7746 | 0,3333 | 0,2910 |
| Árvore com `class_weight="balanced"` (`max_depth=4`) | 0,5199 | 0,4442 | 0,3608 |

**Leitura honesta:** sem `class_weight`, a árvore **não superou o chute na classe
maioritária** — ela aprendeu a prever "Com Vítimas Feridas" para todo mundo, com
recall 0 nas outras duas classes. Com `class_weight="balanced"` ela passa a prever
as três classes e supera a referência em macro-F1 (0,3608 vs 0,2910) e em acurácia
balanceada (0,4442 vs 0,3333), mas a acurácia global cai e a precisão em "Com
Vítimas Fatais" fica em 0,1221.

`class_weight="balanced"` é justificado pelo desbalanceamento do treino (77% / 15% /
7%). Mas as probabilidades desse modelo **não** são risco calibrado, justamente
porque os pesos foram alterados.

**Conclusão metodológica (não causal):** as 9 condições temporais, ambientais e
estruturais disponíveis têm **pouco poder de separação** da gravidade nesta base. O
que decide a gravidade está principalmente em informações que ficaram fora de X de
propósito — quem estava envolvido, tipo de veículo, dinâmica da colisão — e em
fatores que a base simplesmente não registra. Isso é um resultado, não uma falha do
procedimento.

---

## 7. Fontes

- [Dados abertos da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf)
- [Dicionários de dados da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes)
- [Fayyad, Piatetsky-Shapiro e Smyth — *From Data Mining to Knowledge Discovery in Databases*, 1996](https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/view/1230)
- [pandas: `read_csv`](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [scikit-learn: prevenção de vazamento de dados](https://scikit-learn.org/stable/common_pitfalls.html)
- [scikit-learn: `DecisionTreeClassifier`](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html)
- [scikit-learn: `classification_report`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
