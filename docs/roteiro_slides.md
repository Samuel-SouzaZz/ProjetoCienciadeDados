# Roteiro dos slides — Gravidade dos acidentes em rodovias federais

Cada slide tem: o que vai na tela, um rascunho de fala, qual figura usar e de onde
saiu o número. As falas são sugestão — adaptem ao jeito de cada um.

Cuidado na apresentação: não dizer que algo "causa" acidente, não tratar frequência
como risco e não vender o modelo como previsão do futuro.

---

## Slide 1 — Capa

**Conteúdo:** tema, integrantes, curso, semestre, instituição, data.

**Fala:** "Boa noite. A gente aplicou o processo KDD na base de acidentes da PRF
para ver quais características temporais, ambientais e estruturais aparecem
associadas à gravidade."

**Visual:** capa institucional.

**Fonte:** `docs/ficha_tecnica.md`.

---

## Slide 2 — Contextualização

**Conteúdo:** a PRF atende cerca de 70.000 km de rodovias federais; cada
atendimento gera um Boletim de Acidente de Trânsito; esses boletins viram dados
abertos.

**Fala:** "A PRF cobre cerca de setenta mil quilômetros de rodovias. Cada acidente
gera um boletim, e esses boletins são publicados. Sem um processo organizado, esse
volume vira só planilha. O KDD é o caminho que a gente usou para transformar
registro em resposta."

**Visual:** mapa do Brasil ou foto de rodovia; sem inventar número.

**Fonte:** introdução do dicionário oficial da PRF.

---

## Slide 3 — Definição do problema

**Conteúdo:**
- Pergunta: quais características temporais, ambientais e estruturais estão
  associadas à gravidade dos acidentes registrados em rodovias federais?
- Unidade de análise: uma ocorrência de acidente.
- Tarefa: classificação da gravidade.

**Fala:** "A pergunta é essa. Duas palavras importam: 'associadas', não 'causam';
e 'registrados', porque só temos o que aconteceu e foi anotado."

**Visual:** pergunta em destaque, com "associadas" e "registrados" marcados.

---

## Slide 4 — O que a análise não permite

**Conteúdo:**
1. não estima a chance de uma viagem sofrer acidente;
2. frequência não é risco sem dados de exposição;
3. associação não é causa;
4. avaliação retrospectiva não é previsão do futuro.

**Fala:** "Antes dos números: se a maioria dos acidentes é com céu claro, isso
provavelmente só diz que a maioria das viagens é com céu claro. Para falar de risco
precisaríamos saber quantos veículos passaram em cada condição, e isso não está na
base."

**Visual:** quatro frases curtas.

**Fonte:** `docs/planejamento_kdd.md`, seção 1.

---

## Slide 5 — O processo KDD

**Conteúdo:** definição do problema → seleção → pré-processamento → transformação →
mineração.

**Fala:** "Seguimos as cinco etapas do KDD do Fayyad e colegas. Interpretação não
entra nesta entrega, então paramos na mineração proposta."

**Visual:** cinco caixas em sequência.

**Fonte:** Fayyad, Piatetsky-Shapiro e Smyth (1996).

---

## Slide 6 — Conhecendo a base da PRF

**Conteúdo:** tabela de fatos confirmados.

| item | valor |
|---|---|
| Arquivo | `acidentes2025_todas_causas_tipos.csv` |
| Linhas | 584.010 |
| Colunas | 37 |
| Período | 2025-01-01 a 2025-12-31 |
| Separador / codificação / decimal | `;` / `latin-1` / vírgula |
| Ocorrências distintas | 72.529 |
| Pessoas distintas | 188.346 |

**Fala:** "A base tem 584 mil linhas e 37 colunas, cobrindo o ano de 2025.
Mas a informação mais importante deste slide é a próxima linha: essas 584 mil linhas
não são 584 mil acidentes."

**Visual:** tabela; destacar a última linha.

**Fonte:** `reports/diagnostico.md`.

---

## Slide 7 — A descoberta que mudou tudo: a unidade da linha

**Conteúdo:**
- 584.010 linhas ÷ 72.529 acidentes = **8,05 linhas por acidente**;
- o dicionário diz "agregados por pessoa, com todas as causas e tipos";
- somar direto infla os números:

| medida | somando todas as linhas | somando por pessoa distinta |
|---|---|---|
| mortos | 27.912 | **6.043** |
| feridos leves | 179.140 | 63.532 |

**Fala:** "Cada pessoa envolvida aparece repetida uma vez para cada causa e
cada tipo de acidente registrados. Se a gente somasse a coluna 'mortos'
diretamente, encontraria 27.912 mortos. O número correto é 6.043 — quatro vezes e
meia menor. Um erro de uma linha de código produziria uma estatística
completamente falsa, e é por isso que o pré-processamento não é detalhe técnico."

**Visual:** as duas colunas de números lado a lado, com o fator 4,6× em destaque.

**Fonte:** `reports/diagnostico.md`, seção 3.

---

## Slide 8 — Seleção dos atributos escolhidos

**Conteúdo:** as 9 entradas permitidas, por grupo:

| grupo | atributos |
|---|---|
| Temporal | `dia_semana`, `faixa_horaria`, `fim_de_semana`, `mes` |
| Ambiental | `fase_dia`, `condicao_metereologica` |
| Estrutural | `tipo_pista`, `tracado_via`, `uso_solo` |

Alvo: `classificacao_acidente` — Sem Vítimas, Com Vítimas Feridas, Com Vítimas
Fatais.

**Fala:** "Escolhemos nove atributos, e eles cobrem exatamente os três
grupos da nossa pergunta: temporal, ambiental e estrutural. A lista é explícita: nada
entra no modelo por exclusão."

**Visual:** três colunas coloridas por grupo.

**Fonte:** `config/regras_qualidade.json`, campo `entradas_modelo_permitidas`.

---

## Slide 9 — Variáveis descartadas e por quê

**Conteúdo:** quatro motivos de descarte, com exemplos:

| motivo | exemplos | por que |
|---|---|---|
| Vazamento da resposta | `mortos`, `feridos_leves`, `feridos_graves`, `ilesos`, `estado_fisico` | entregam a gravidade ao algoritmo |
| Identificador ou metadado | `id`, `regional`, `delegacia`, `uop`, `latitude`, `longitude` | rastreabilidade e administração |
| Apuração posterior | `causa_acidente`, `tipo_acidente`, `tipo_veiculo`, `marca` | descrevem o acidente já apurado |
| Recorte não modelado | `uf` | usada para contexto, não como entrada |

**Fala:** "O descarte mais importante é o primeiro. Se colocássemos a coluna
'mortos' entre as entradas, o modelo acertaria quase tudo — e não teria aprendido
nada, porque 'ter morto' é a própria definição de 'com vítimas fatais'. Isso se chama
vazamento de dados. Deixamos também causa e tipo de acidente de fora, porque são
conclusões que o policial escreve depois do acidente, e não condições que existiam
antes. Descartar aqui significa tirar do modelo: nenhum dado original foi apagado."

**Visual:** tabela com os quatro motivos.

**Fonte:** `docs/planejamento_kdd.md`, seção 3.

---

## Slide 10 — Pré-processamento: os problemas encontrados

**Conteúdo:** seis achados reais:

| problema | evidência |
|---|---|
| A linha não é uma ocorrência | 8,05 linhas por acidente |
| Arquivo não é UTF-8 | o byte do "ç" quebra a leitura UTF-8 |
| `tracado_via` multivalorado sem ordem fixa | 605 rótulos para 12 componentes |
| Ausência disfarçada de categoria | "Ignorado", "Não Informado", "NA/NA", ano `0` |
| Idade impossível | 432 registros com idade acima de 120 (até 2024) |
| Gravidade ausente | 1 ocorrência |

E o que **não** era problema: 0 duplicatas exatas, 0 erros de formato, 0 conflitos
de chave.

**Fala:** "Fizemos um diagnóstico antes de limpar. Um exemplo simples: o
campo de traçado da via aceita vários valores separados por ponto e vírgula, e a
ordem varia. 'Reta;Declive' e 'Declive;Reta' são o mesmo traçado, mas o computador
enxerga dois rótulos diferentes. Isso gerava 605 rótulos distintos para apenas 12
componentes reais."

**Visual:** tabela; destacar "605 → 230".

**Fonte:** `reports/diagnostico.md` e `reports/limpeza.md`.

---

## Slide 11 — Pré-processamento: as correções

**Conteúdo:**

| ação | volume |
|---|---|
| Leitura correta (`;`, latin-1, decimal `,`) | 584.010 linhas, 0 ilegíveis |
| Tokens de ausência por coluna | 128.336 células |
| Mapas explícitos de categoria | `dia_semana` e `uso_solo`: todas as linhas |
| Ordenação de `tracado_via` | 605 → 230 rótulos |
| Idade impossível → ausência (original preservado) | 432 registros |
| Agregação por ocorrência | 584.010 → 72.529 |
| Reconciliação das linhas | soma dos destinos = entrada ✔ |

O que **não** fizemos: `fillna(0)` global, imputar a gravidade, remover linha por
ter alguma ausência.

**Fala:** "Cada correção é uma regra escrita, repetível e auditada. O
registro de auditoria guarda arquivo de origem, identificador, regra aplicada, valor
antes e valor depois. E a reconciliação prova que nenhuma linha desapareceu no
caminho: entrada igual a duplicatas mais quarentena mais mantidas."

**Visual:** tabela + selo "0 linhas perdidas".

**Fonte:** `reports/limpeza.md`, `reports/auditoria_limpeza.csv`.

---

## Slide 12 — Validação independente

**Conteúdo:**
- um script separado **reabre** o CSV salvo e aplica o contrato de qualidade;
- ele **não** corrige nada durante a verificação;
- **177 regras** avaliadas: 175 passaram, 2 avisos;
- status: **APROVADA COM RESSALVAS**;
- ressalvas: 175 ocorrências com `km` abaixo do mínimo do dicionário; 5 ocorrências
  sem veículo identificado;
- o próprio validador é testado com 19 casos sintéticos.

**Fala:** "Limpar sozinho não basta — alguém tem que conferir. Fizemos um
verificador separado que reabre o arquivo e testa 177 regras. Ele não corrige nada,
só aponta. Também testamos o próprio verificador com arquivos falsos (data 30 de
fevereiro, categoria inventada, contagem negativa) para ver se ele realmente
reprova. Aprovado com ressalvas não quer dizer 'perfeito': as duas ressalvas estão
escritas no relatório."

**Visual:** selo de status + as duas ressalvas.

**Fonte:** `reports/validacao.md`, `tests/test_validacao.py`.

---

## Slide 13 — Transformação

**Conteúdo:**
- derivados: `mes`, `fim_de_semana`, `faixa_horaria`;
- limites: Madrugada 00:00–05:59:59 · Manhã 06:00–11:59:59 · Tarde 12:00–17:59:59 ·
  Noite 18:00–23:59:59;
- aviso: `faixa_horaria` (relógio) ≠ `fase_dia` (registro da PRF).

**Fala:** "Criamos a faixa horária dividindo o relógio em quatro blocos.
Atenção a uma confusão fácil: faixa horária não é a mesma coisa que fase do dia. A
fase do dia é o que o policial anotou — amanhecer, pleno dia, anoitecer, plena
noite. Um acidente às dezoito e trinta pode ser 'Noite' no relógio e 'Anoitecer' no
registro. São duas informações diferentes, e mantivemos as duas."

**Visual:** régua de 24 horas com os quatro blocos.

**Fonte:** `config/regras_qualidade.json`, campo `limites`.

---

## Slide 14 — Tabela Antes × Depois (registros fictícios)

**Conteúdo:** as duas tabelas com F01–F05 e o aviso
**"Exemplo fictício — não representa resultados da PRF"**.

O que cada registro demonstra:

| ref | problema | regra |
|---|---|---|
| F01 | `sábado` minúsculo, `uso_solo` = "Sim", UF minúscula | mapas explícitos |
| F02 | `tracado_via` = "Reta;Declive" | ordenação dos componentes |
| F03 | clima = "Ignorado" | token de ausência |
| F04 | espaços sobrando, sentido "Não Informado" | limpeza de texto + token |
| F05 | gravidade vazia | alvo não imputado; registro fica inelegível |

**Fala:** "Estes cinco registros são inventados, e o aviso está na tela para
ninguém confundir. Eles servem para mostrar cada regra em ação. O caso F05 é o mais
importante: quando a gravidade está em branco, nós não inventamos um valor. O
registro fica na base marcado como inelegível e sai do treino, com o motivo
contado."

**Visual:** `reports/exemplo_antes.png` e `reports/exemplo_antes_depois.png`.

**Fonte:** `reports/exemplo_ficticio.md`.

---

## Slide 14b — Antes × Depois com dados reais (opcional, mas recomendado)

Este slide é a resposta para quem perguntar "mas isso funciona nos dados de
verdade?". Os `id` são os do arquivo original, então dá para abrir a base bruta na
hora e conferir.

**Conteúdo:** duas partes, cada uma rendendo um slide se houver tempo.

**Parte 1 — por que agregar (a mais forte):** a ocorrência `id=654535` ocupa **8
linhas** no arquivo bruto, porque é 1 pessoa × 4 causas × 2 tipos de acidente. Todas
as 8 linhas trazem `mortos = 1`.

**Fala:** "Olhem a coluna destacada. São oito linhas, todas com `mortos`
igual a 1. Se eu somar a coluna, eu concluo que morreram oito pessoas neste
acidente. Morreu uma. É o mesmo condutor repetido oito vezes, uma vez para cada
combinação de causa e tipo. Por isso a contagem de vítimas é feita sobre pares
`(id, pesid)` distintos, e não somando linhas. Sem esse cuidado, todo número de
mortos deste trabalho estaria errado."

**Visual:** `reports/exemplo_real_agregacao_antes.png` e
`reports/exemplo_real_agregacao_depois.png`.

**Parte 2 — o que muda dentro da célula:** cinco ocorrências reais, uma por tipo de
problema, e a lista das células alteradas com a regra responsável por cada uma.

**Fala:** "Aqui não tem exemplo inventado. `quinta-feira` virou
`Quinta-feira`, `Reta;Declive` virou `Declive;Reta` para a mesma via não aparecer
como duas categorias, `uso_solo` deixou de ser `Sim`/`Não` e passou a dizer
`Urbano`/`Rural` como manda o dicionário da PRF, e `Ignorado` virou célula vazia,
porque não saber o clima não é um tipo de clima. Cada linha dessa tabela tem uma
regra com nome, e esse nome está no arquivo de auditoria."

**Visual:** `reports/exemplo_real_mudancas.png` (a mais didática);
`reports/exemplo_real_antes.png` e `reports/exemplo_real_depois.png` se quiser mostrar
as ocorrências inteiras; `reports/exemplo_real_derivados.png` para os atributos novos.

**Fonte:** `reports/exemplo_real.md`.

---

## Slide 15 — Base legível, X e y são coisas diferentes

**Conteúdo:**
1. base legível: `prf_limpo.csv`, rótulos em português;
2. X transformado: matriz numérica do `OneHotEncoder`, ajustada só no treino;
3. y: só a coluna da gravidade das linhas elegíveis.

Recorte da codificação one-hot.

**Fala:** "O algoritmo não lê 'Céu Claro'. Ele precisa de números. A
codificação transforma cada categoria em uma coluna de zeros e uns. Mas essa matriz
não é o nosso arquivo de entrega: a base legível continua em português, para
qualquer pessoa conferir."

**Visual:** `reports/exemplo_codificacao.png`.

---

## Slide 16 — Mineração proposta

**Conteúdo:**
- técnica: árvore de decisão de classificação;
- por que: tarefa categórica e regras legíveis;
- proteções: divisão 80/20 estratificada **antes** de transformar; Pipeline ajustado
  só no treino; `handle_unknown="ignore"`; `max_depth` escolhido por validação
  cruzada no treino; `random_state=42`;
- referência obrigatória: `DummyClassifier(most_frequent)`;
- métricas: matriz de confusão, F1 por classe, macro-F1, acurácia balanceada.

**Fala:** "Escolhemos árvore de decisão por dois motivos: a tarefa é categórica e
dá para ler as regras. Outro cuidado: a divisão treino/teste acontece antes de
qualquer transformação que aprenda com os dados. Se o codificador visse o teste,
o resultado ficaria otimista sem ser verdadeiro."

**Visual:** fluxo: dados elegíveis → divisão → Pipeline no treino → avaliação no
teste.

**Fonte:** `docs/planejamento_kdd.md`, seção 6.

---

## Slide 17 — Distribuição das classes (resultado opcional do código)

**Conteúdo:** 72.529 ocorrências:

| gravidade | ocorrências | % |
|---|---|---|
| Com Vítimas Feridas | 56.181 | 77,46 |
| Sem Vítimas | 11.138 | 15,36 |
| Com Vítimas Fatais | 5.209 | 7,18 |
| (ausente) | 1 | 0,001 |

**Fala:** "As classes são bem desbalanceadas: quase 78% são acidentes com
vítimas feridas. Guardem esse número, porque ele vai reaparecer no próximo slide de
um jeito incômodo."

**Visual:** `reports/figuras/01_distribuicao_classes.png` (barras) **ou**, se preferir
proporção no projetor, `09_pizza_gravidade.png` / `10_rosca_gravidade.png`.

**Fonte:** `reports/tabela_distribuicao_classes.csv`.

> **Banco de figuras extras (mesmo número, outro estilo):** pizza e rosca da
> gravidade; barras horizontais de volume por dia, faixa horária e clima; barras
> agrupadas por tipo de pista; heatmaps de faixa horária e dia da semana; pizzas
> lado a lado para uso do solo, fim de semana e tipo de pista. Estão em
> `reports/figuras/` com prefixos `09` a `19`. A tabela de “quando usar cada uma”
> está em `reports/analise.md`.

---

## Slide 18 — Resultado real da execução (resultado opcional do código)

**Conteúdo:**

| execução | acurácia global | acurácia balanceada | macro-F1 |
|---|---|---|---|
| Árvore sem pesos | 0,7746 | 0,3333 | 0,2910 |
| Chute na classe maioritária | 0,7746 | 0,3333 | 0,2910 |
| Árvore com `class_weight="balanced"` | 0,5199 | 0,4442 | 0,3608 |

**Fala:** "Aqui está o resultado real, inclusive a parte ruim. A árvore sem
ajuste de pesos alcançou 77% de acurácia — exatamente o mesmo que chutar sempre a
classe mais comum. Ou seja, ela não aprendeu nada útil. Quando equilibramos os pesos
das classes, ela passou a acertar as três, e superou a referência no macro-F1, mas a
acurácia global caiu. A conclusão metodológica é que as nove condições disponíveis
têm pouco poder para separar a gravidade nesta base — e isso é um resultado válido,
não um erro nosso. Se tivéssemos escondido esse número, o trabalho seria pior."

**Visual:** `reports/modelo_balanceado/matriz_confusao.png`.

**Fonte:** `reports/modelo/modelo.md` e `reports/modelo_balanceado/modelo.md`.

---

## Slide 19 — Aplicação social (condicional)

**Conteúdo:** como o planejamento **poderia** apoiar prevenção, fiscalização e
políticas públicas.

**Fala:** "Se este planejamento fosse combinado com dados de exposição ao
trânsito, ele poderia apoiar decisões de fiscalização e sinalização. No condicional,
de propósito: com os dados que temos, conseguimos descrever como os acidentes
registrados se distribuem, e isso já ajuda a formular hipóteses e a decidir que
dados faltam coletar."

**Visual:** três ícones: prevenção, fiscalização, políticas públicas.

---

## Slide 20 — Conclusão e reflexão

**Conteúdo:**
- o que fizemos: as cinco etapas do KDD, com base limpa validada por 177 regras;
- o que aprendemos: o pré-processamento decide a validade do resultado (o caso dos
  27.912 mortos contra 6.043);
- pergunta ao público: **"como os dados poderiam ajudar a prevenir acidentes
  graves?"**

**Fala:** "O que mais pesou no trabalho não foi o modelo, foi cuidado com os dados.
O mesmo arquivo dava 27.912 mortos ou 6.043, dependendo de a gente entender o que
cada linha representava. Fica a pergunta: como esses dados poderiam ajudar a
prevenir acidentes graves?"

**Visual:** a pergunta em tela cheia.

---

## Slide 21 — Referências

- Dados abertos da PRF: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf
- Dicionários de dados da PRF: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes
- Fayyad, U.; Piatetsky-Shapiro, G.; Smyth, P. *From Data Mining to Knowledge
  Discovery in Databases*. AI Magazine, 1996.
- pandas — `read_csv`: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- scikit-learn — prevenção de vazamento: https://scikit-learn.org/stable/common_pitfalls.html
- scikit-learn — `DecisionTreeClassifier`: https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html
- scikit-learn — `classification_report`: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html

---

## Slide 22 — Ficha técnica

**Conteúdo:** ver `docs/ficha_tecnica.md`. Campos não informados ficam para o grupo
preencher.

---

## Sugestão de divisão das falas

| pessoa | o que fez no trabalho | slides |
|---|---|---|
| Samuel Souza | roteiro, design e documentação | 1–4 |
| Junior Oliveira | roteiro, montagem e organização dos slides | 5–7 |
| Liandra Rodrigues | apresentação e edição dos slides | 8–9 |
| Karolline Oliveira | apresentação dos slides | 10–12 |
| Matheus Oliveira | apresentação dos slides | 13–16 |
| todos | resultados e encerramento | 17–20 |

No slide 20 todo mundo responde a pergunta final. Podem trocar se quiserem.
