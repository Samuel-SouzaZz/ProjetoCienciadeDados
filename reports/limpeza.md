# Limpeza e transformacao - antes x depois

- Entrada: `C:\Users\Administrator\Desktop\Ciencia de dados\data\raw\acidentes2025_todas_causas_tipos.csv`
- SHA-256 da entrada: `b48968a8017a9abda7b6149c894554c7cc3ca1c09257c7dedf2937ebce02e0d3`
- Saida: `C:\Users\Administrator\Desktop\Ciencia de dados\data\processed\prf_limpo.csv`
- SHA-256 da saida: `0a028fe02ec748e115ab5e4d0d4d3cda3b6ae034a5b26deaebc69d267fa3d4ed`
- Contrato: versao 1.0.0
- Execucao: 2026-09-12T14:37:33-03:00

## Reconciliacao das linhas de entrada

- Linhas de entrada: 584010
- Duplicatas exatas removidas: 0
- Linhas em quarentena: 0
- Linhas mantidas e agregadas: 584010
- Soma dos destinos igual a entrada: **True**
- Ocorrencias resultantes: 72529
- Pessoas distintas resultantes: 177479

## Tabela antes x depois

| metrica | antes | depois |
|---|---|---|
| unidade do registro | pessoa x causa x tipo | ocorrencia de acidente |
| linhas | 584010 | 72529 |
| colunas | 37 | 44 |
| ids distintos | 72529 | 72529 |
| duplicatas exatas | 0 | 0 |
| rotulos distintos em tracado_via | 605 | 230 |
| categorias de dia_semana | domingo, quarta-feira, quinta-feira, segunda-feira, sexta-feira, sábado, terça-feira | Domingo, Quarta-feira, Quinta-feira, Segunda-feira, Sexta-feira, Sábado, Terça-feira |
| categorias de uso_solo | Não, Sim | Rural, Urbano |
| celulas de texto corrigidas | - | 201 |
| registros na auditoria | - | 20633 |
| nulos em classificacao_acidente | 7 | 1 |
| nulos em condicao_metereologica | 0 | 1000 |
| nulos em sentido_via | 0 | 167 |
| nulos em fase_dia | 0 | 0 |
| nulos em tipo_pista | 0 | 0 |
| nulos em tracado_via | 0 | 0 |
| nulos em uso_solo | 0 | 0 |
| nulos em km | 1444 | 167 |
| nulos em br | 1444 | 167 |

## Composicao das classes

| classificacao_acidente | base_limpa | elegiveis_para_treino | pct_base_limpa | pct_elegiveis |
|---|---|---|---|---|
| Com Vítimas Fatais | 5209 | 5209 | 7.182 | 7.182 |
| Com Vítimas Feridas | 56181 | 56181 | 77.46 | 77.461 |
| Sem Vítimas | 11138 | 11138 | 15.357 | 15.357 |
|  | 1 | 0 | 0.001 | 0.0 |

## Passos executados

### 1_leitura

```json
{
  "linhas_lidas": 584010,
  "colunas_lidas": 37,
  "linhas_ilegiveis": 0,
  "observacao": "O pandas nao reportou linha ilegivel. Todas as colunas foram lidas como texto."
}
```

### 2_cabecalhos

```json
{
  "mapa_original_para_padronizado": {
    "id": "id",
    "pesid": "pesid",
    "data_inversa": "data_inversa",
    "dia_semana": "dia_semana",
    "horario": "horario",
    "uf": "uf",
    "br": "br",
    "km": "km",
    "municipio": "municipio",
    "causa_principal": "causa_principal",
    "causa_acidente": "causa_acidente",
    "ordem_tipo_acidente": "ordem_tipo_acidente",
    "tipo_acidente": "tipo_acidente",
    "classificacao_acidente": "classificacao_acidente",
    "fase_dia": "fase_dia",
    "sentido_via": "sentido_via",
    "condicao_metereologica": "condicao_metereologica",
    "tipo_pista": "tipo_pista",
    "tracado_via": "tracado_via",
    "uso_solo": "uso_solo",
    "id_veiculo": "id_veiculo",
    "tipo_veiculo": "tipo_veiculo",
    "marca": "marca",
    "ano_fabricacao_veiculo": "ano_fabricacao_veiculo",
    "tipo_envolvido": "tipo_envolvido",
    "estado_fisico": "estado_fisico",
    "idade": "idade",
    "sexo": "sexo",
    "ilesos": "ilesos",
    "feridos_leves": "feridos_leves",
    "feridos_graves": "feridos_graves",
    "mortos": "mortos",
    "latitude": "latitude",
    "longitude": "longitude",
    "regional": "regional",
    "delegacia": "delegacia",
    "uop": "uop"
  },
  "renomeadas": [],
  "colisoes": []
}
```

### 3_texto

```json
{
  "celulas_alteradas": 201
}
```

### 4_tokens_ausencia

```json
{
  "condicao_metereologica": {
    "tokens": [
      "Ignorado"
    ],
    "celulas_convertidas": 7130
  },
  "sentido_via": {
    "tokens": [
      "Não Informado"
    ],
    "celulas_convertidas": 1444
  },
  "estado_fisico": {
    "tokens": [
      "Não Informado"
    ],
    "celulas_convertidas": 35083
  },
  "sexo": {
    "tokens": [
      "Não Informado",
      "Ignorado",
      "Inválido"
    ],
    "celulas_convertidas": 36254
  },
  "marca": {
    "tokens": [
      "NA/NA"
    ],
    "celulas_convertidas": 18617
  },
  "ano_fabricacao_veiculo": {
    "tokens": [
      "0"
    ],
    "celulas_convertidas": 29808
  }
}
```

### 5_categorias

```json
{
  "dia_semana": 584010,
  "uso_solo": 584010,
  "fase_dia": 324063,
  "tipo_pista": 0,
  "condicao_metereologica": 0,
  "sentido_via": 0,
  "tracado_via_celulas_reordenadas": 108266,
  "tracado_via_rotulos_antes": 605,
  "tracado_via_rotulos_depois": 230
}
```

### 6_campos_impossiveis

```json
{
  "idade_fora_do_intervalo": 432,
  "intervalo_adotado": [
    0,
    120
  ],
  "arquivo": "C:\\Users\\Administrator\\Desktop\\Ciencia de dados\\data\\quarantine\\campos_para_revisao.csv",
  "observacao": "Regra deste projeto, nao do dicionario. O registro NAO foi excluido: apenas o valor impossivel virou ausencia, com o original na auditoria."
}
```

### 7_integridade_chave

```json
{
  "ids_avaliados": 72529,
  "ids_com_conflito": 0,
  "conflitos_por_coluna": {
    "data_inversa": 0,
    "dia_semana": 0,
    "horario": 0,
    "uf": 0,
    "br": 0,
    "km": 0,
    "municipio": 0,
    "classificacao_acidente": 0,
    "fase_dia": 0,
    "sentido_via": 0,
    "condicao_metereologica": 0,
    "tipo_pista": 0,
    "tracado_via": 0,
    "uso_solo": 0,
    "latitude": 0,
    "longitude": 0,
    "regional": 0,
    "delegacia": 0,
    "uop": 0
  }
}
```

### 9_derivados

```json
{
  "datas_que_falharam_na_conversao": 0,
  "horarios_que_falharam_na_conversao": 0,
  "dia_semana_divergente": 0,
  "limites_faixa_horaria": {
    "Madrugada": "00:00:00 a 05:59:59",
    "Manha": "06:00:00 a 11:59:59",
    "Tarde": "12:00:00 a 17:59:59",
    "Noite": "18:00:00 a 23:59:59"
  }
}
```

### 10_elegibilidade

```json
{
  "ocorrencias": 72529,
  "alvo_ausente": 1,
  "elegiveis_para_treino": 72528,
  "inelegiveis": 1,
  "com_alguma_entrada_ausente": 1000,
  "regra": "Somente alvo ausente torna a ocorrencia inelegivel. Ausencia em entrada e imputada dentro do Pipeline, ajustado apenas no treino."
}
```
