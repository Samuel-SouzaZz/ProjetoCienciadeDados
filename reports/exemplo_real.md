# Recortes ANTES x DEPOIS com dados reais

> Diferente do exemplo F01–F05, as linhas daqui são reais e dá para conferir pelo `id` no arquivo bruto.

## 1. Agregacao: de varias linhas para uma ocorrencia

A ocorrencia **id=654535** ocupa **8 linhas** no arquivo bruto, porque o arquivo repete a ocorrencia uma vez para cada combinacao de (pessoa x causa x tipo de acidente): sao 1 pessoa(s), 4 causa(s) e 2 tipo(s).

Consequencia pratica: somar a coluna `mortos` linha a linha resulta em **8 mortos**, mas a ocorrencia teve **1** vitima fatal. A contagem correta exige contar pares `(id, pesid)` distintos, e e isso que `src/limpeza.py` faz.

### ANTES (linhas brutas)

| pesid | tipo_envolvido | causa_acidente | ordem_tipo_acidente | tipo_acidente | estado_fisico | ilesos | feridos_leves | mortos |
|---|---|---|---|---|---|---|---|---|
| 1473278 | Condutor | Iluminação deficiente | 2 | Queda de ocupante de veículo | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Iluminação deficiente | 1 | Capotamento | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Ausência de reação do condutor | 2 | Queda de ocupante de veículo | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Ausência de reação do condutor | 1 | Capotamento | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Velocidade Incompatível | 2 | Queda de ocupante de veículo | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Velocidade Incompatível | 1 | Capotamento | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Ingestão de álcool pelo condutor | 2 | Queda de ocupante de veículo | Óbito | 0 | 0 | 1 |
| 1473278 | Condutor | Ingestão de álcool pelo condutor | 1 | Capotamento | Óbito | 0 | 0 | 1 |

### DEPOIS (linha unica na base limpa)

| id | qtd_pessoas | qtd_ilesos | qtd_feridos_leves | qtd_feridos_graves | qtd_mortos | qtd_causas_distintas | qtd_tipos_distintos | classificacao_acidente |
|---|---|---|---|---|---|---|---|---|
| 654535 | 1 | 0 | 0 | 0 | 1 | 4 | 2 | Com Vítimas Fatais |

Figuras: `exemplo_real_agregacao_antes.png` e `exemplo_real_agregacao_depois.png`.

## 2. Padronizacao: o que muda dentro da celula

Ocorrencias usadas: `668490`, `692901`, `703270`, `716698`, `730331`. Cada uma foi escolhida por exibir um problema diferente encontrado no diagnostico.

### ANTES

| id | data_inversa | dia_semana | horario | uf | fase_dia | condicao_metereologica | tipo_pista | tracado_via | uso_solo | sentido_via | classificacao_acidente |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 668490 | 2025-03-20 | quinta-feira | 18:20:00 | GO | Anoitecer | Chuva | Simples | Reta;Declive | Não | Crescente | Sem Vítimas |
| 692901 | 2025-05-22 | quinta-feira | 08:30:00 | MG | Pleno dia | Ignorado | Dupla | Curva;Aclive | Não | Decrescente | Com Vítimas Feridas |
| 703270 | 2025-07-07 | segunda-feira | 18:20:00 | PE | Plena Noite | Céu Claro | Simples | Reta | Não | Não Informado | Sem Vítimas |
| 716698 | 2025-09-06 | sábado | 23:45:00 | PB | Plena Noite | Chuva | Dupla | Reta | Sim | Decrescente | Sem Vítimas |
| 730331 | 2025-11-08 | sábado | 04:30:00 | MG | Amanhecer | Nublado | Simples | Declive;Curva | Não | Crescente | Com Vítimas Fatais |

### DEPOIS

| id | data_inversa | dia_semana | faixa_horaria | fim_de_semana | mes_nome | uf | fase_dia | condicao_metereologica | tipo_pista | tracado_via | uso_solo | sentido_via | classificacao_acidente | elegivel_modelo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 668490 | 2025-03-20 | Quinta-feira | Noite | Não | Março | GO | Anoitecer | Chuva | Simples | Declive;Reta | Rural | Crescente | Sem Vítimas | Sim |
| 692901 | 2025-05-22 | Quinta-feira | Manhã | Não | Maio | MG | Pleno Dia | (vazio) | Dupla | Aclive;Curva | Rural | Decrescente | Com Vítimas Feridas | Sim |
| 703270 | 2025-07-07 | Segunda-feira | Noite | Não | Julho | PE | Plena Noite | Céu Claro | Simples | Reta | Rural | (vazio) | Sem Vítimas | Sim |
| 716698 | 2025-09-06 | Sábado | Noite | Sim | Setembro | PB | Plena Noite | Chuva | Dupla | Reta | Urbano | Decrescente | Sem Vítimas | Sim |
| 730331 | 2025-11-08 | Sábado | Madrugada | Sim | Novembro | MG | Amanhecer | Nublado | Simples | Curva;Declive | Rural | Crescente | Com Vítimas Fatais | Sim |

### Somente as celulas que mudaram

| id | coluna | antes (arquivo bruto) | depois (base limpa) | regra aplicada |
|---|---|---|---|---|
| 668490 | dia_semana | quinta-feira | Quinta-feira | mapa_dia_semana |
| 668490 | tracado_via | Reta;Declive | Declive;Reta | ordenacao_componentes |
| 668490 | uso_solo | Não | Rural | mapa_uso_solo_dicionario |
| 692901 | dia_semana | quinta-feira | Quinta-feira | mapa_dia_semana |
| 692901 | fase_dia | Pleno dia | Pleno Dia | mapa_fase_dia |
| 692901 | condicao_metereologica | Ignorado | (vazio) | token_ausencia |
| 692901 | tracado_via | Curva;Aclive | Aclive;Curva | ordenacao_componentes |
| 692901 | uso_solo | Não | Rural | mapa_uso_solo_dicionario |
| 703270 | dia_semana | segunda-feira | Segunda-feira | mapa_dia_semana |
| 703270 | sentido_via | Não Informado | (vazio) | token_ausencia |
| 703270 | uso_solo | Não | Rural | mapa_uso_solo_dicionario |
| 716698 | dia_semana | sábado | Sábado | mapa_dia_semana |
| 716698 | uso_solo | Sim | Urbano | mapa_uso_solo_dicionario |
| 730331 | dia_semana | sábado | Sábado | mapa_dia_semana |
| 730331 | tracado_via | Declive;Curva | Curva;Declive | ordenacao_componentes |
| 730331 | uso_solo | Não | Rural | mapa_uso_solo_dicionario |

### Atributos derivados (nao existiam no bruto)

| id | mes_nome (novo) | faixa_horaria (novo) | fim_de_semana (novo) | elegivel_modelo (novo) |
|---|---|---|---|---|
| 668490 | Março | Noite | Não | Sim |
| 692901 | Maio | Manhã | Não | Sim |
| 703270 | Julho | Noite | Não | Sim |
| 716698 | Setembro | Noite | Sim | Sim |
| 730331 | Novembro | Madrugada | Sim | Sim |

Figuras: `exemplo_real_antes.png`, `exemplo_real_depois.png`, `exemplo_real_mudancas.png` e `exemplo_real_derivados.png`.

## Como conferir na apresentacao

1. Abrir `data/raw/acidentes2025_todas_causas_tipos.csv` e filtrar pelo `id`.
2. Abrir `data/processed/prf_limpo.csv` e filtrar pelo mesmo `id`.
3. Comparar com a tabela de mudancas acima: cada celula alterada tem regra correspondente em `config/regras_qualidade.json` e aparece no registro de auditoria `reports/auditoria_limpeza.csv`.
