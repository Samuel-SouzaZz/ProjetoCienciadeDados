# Tabela ANTES x DEPOIS (registros ficticios F01-F05)

> **Exemplo fictício — não representa resultados da PRF**

Estes cinco registros nao entram nos graficos reais, no treinamento nem nas metricas. Servem apenas para mostrar o efeito das regras.

## O que cada registro demonstra

| ref | problema exibido | regra aplicada |
|---|---|---|
| F01 | `dia_semana` em minusculas, `uso_solo` como "Sim", `fase_dia` como "Pleno dia", UF em minusculas | mapeamentos explicitos + UF em maiusculas |
| F02 | `tracado_via` multivalorado fora de ordem ("Reta;Declive") | ordenacao alfabetica dos componentes |
| F03 | `condicao_metereologica` = "Ignorado" (ausencia disfarcada de categoria) | token de ausencia por coluna |
| F04 | espacos sobrando no texto e `sentido_via` = "Nao Informado" | limpeza de texto + token de ausencia |
| F05 | `classificacao_acidente` vazia | alvo NAO imputado; registro fica inelegivel |

## ANTES

| ref | dia_semana | horario | uf | fase_dia | condicao_metereologica | tracado_via | uso_solo | sentido_via | classificacao_acidente |
|---|---|---|---|---|---|---|---|---|---|
| F01 | sábado | 23:40:00 | mg | Pleno dia | Céu Claro | Reta | Sim | Crescente | Com Vítimas Feridas |
| F02 | quarta-feira | 07:15:00 | PR | Amanhecer | Chuva | Reta;Declive | Não | Decrescente | Sem Vítimas |
| F03 | domingo | 03:05:00 | BA | Plena Noite | Ignorado | Curva;Aclive | Não | Crescente | Com Vítimas Fatais |
| F04 |  segunda-feira  | 14:50:00 | sp | Pleno dia |   Nublado  | Interseção de Vias;Reta | Sim | Não Informado | Com Vítimas Feridas |
| F05 | sábado | 18:30:00 | RS | Anoitecer | Nevoeiro/Neblina | Reta;Ponte | Não | Decrescente |  |

## DEPOIS

| ref | dia_semana | faixa_horaria | fim_de_semana | mes_nome | uf | fase_dia | condicao_metereologica | tracado_via | uso_solo | sentido_via | classificacao_acidente | elegivel_modelo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | Sábado | Noite | Sim | Janeiro | MG | Pleno Dia | Céu Claro | Reta | Urbano | Crescente | Com Vítimas Feridas | Sim |
| F02 | Quarta-feira | Manhã | Não | Março | PR | Amanhecer | Chuva | Declive;Reta | Rural | Decrescente | Sem Vítimas | Sim |
| F03 | Domingo | Madrugada | Sim | Junho | BA | Plena Noite |  | Aclive;Curva | Rural | Crescente | Com Vítimas Fatais | Sim |
| F04 | Segunda-feira | Tarde | Não | Setembro | SP | Pleno Dia | Nublado | Interseção de Vias;Reta | Urbano |  | Com Vítimas Feridas | Sim |
| F05 | Sábado | Noite | Sim | Dezembro | RS | Anoitecer | Nevoeiro/Neblina | Ponte;Reta | Rural | Decrescente |  | Não |

## Recorte da codificacao categorica

| ref | faixa_horaria_Madrugada | faixa_horaria_Manhã | faixa_horaria_Noite | faixa_horaria_Tarde | tipo_pista_Dupla | tipo_pista_Múltipla | tipo_pista_Simples | uso_solo_Rural | uso_solo_Urbano |
|---|---|---|---|---|---|---|---|---|---|
| F01 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1 |
| F02 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| F03 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| F04 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 |
| F05 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 0 |

## Tres objetos diferentes

- **base legivel** (`prf_limpo.csv`): rotulos em portugues, para ler e conferir.
- **X transformado**: matriz numerica produzida pelo OneHotEncoder dentro do Pipeline, ajustada SOMENTE no treino. Nao e um arquivo para leitura humana.
- **y**: apenas a coluna `classificacao_acidente` das linhas elegiveis.

## Padronizacao de formato x normalizacao numerica

- **Padronizar formato** e deixar data como `aaaa-mm-dd`, hora como `HH:MM:SS`, UF em maiusculas e categorias com grafia unica. E o que este projeto faz.
- **Normalizar/padronizar escala** e transformar numeros para media 0 e desvio 1 (ou para o intervalo 0-1). Arvore de decisao NAO precisa disso, porque decide por limiares em cada atributo, sem comparar magnitudes entre colunas diferentes.

## Limites das faixas horarias

- Madrugada: 00:00:00 a 05:59:59
- Manha: 06:00:00 a 11:59:59
- Tarde: 12:00:00 a 17:59:59
- Noite: 18:00:00 a 23:59:59

> `faixa_horaria` e faixa de RELOGIO. `fase_dia` e a fase de luz registrada pelo policial (Amanhecer, Pleno Dia, Anoitecer, Plena Noite). Sao coisas diferentes: um acidente as 18:30 pode estar em "Noite" e, ao mesmo tempo, em "Anoitecer".
