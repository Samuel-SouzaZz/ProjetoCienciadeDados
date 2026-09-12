# Diagnostico da base bruta da PRF

- Arquivo: `C:\Users\Administrator\Desktop\Ciencia de dados\data\raw\acidentes2025_todas_causas_tipos.csv`
- SHA-256: `b48968a8017a9abda7b6149c894554c7cc3ca1c09257c7dedf2937ebce02e0d3`
- Execucao: 2026-09-12T14:41:20-03:00
- Leitura: separador `;`, encoding `latin-1`, decimal `,`

## 1. Forma

- Linhas: **584010**
- Colunas: **37**
- Nomes duplicados: nenhum

## 2. Unidade de cada linha

- Linhas: 584010
- IDs de acidente distintos: 72529
- Pares (id, pesid) distintos: 188346
- Combinacoes (id, pesid, causa, ordem_tipo) distintas: 560828
- Media de linhas por ocorrencia: 8.052

> Como as linhas por ocorrencia sao muitas, o arquivo NAO esta na unidade 'uma linha = um acidente'. Agregar por `id` e obrigatorio antes da analise por ocorrencia, e `id` repetido NAO significa duplicata.

## 3. Somas de vitimas: ingenua x deduplicada

| medida | soma de todas as linhas | soma por (id, pesid) |
|---|---|---|
| mortos | 27912 | 6043 |
| feridos_leves | 179140 | 63532 |
| feridos_graves | 66983 | 20018 |
| ilesos | 218091 | 76406 |

A soma ingenua superestima porque cada pessoa aparece repetida uma vez por combinacao de causa e tipo de acidente.

## 4. Duplicatas exatas

- Linhas identicas excedentes: 0
- Grupos com linhas identicas: 0

## 5. Conflitos de chave (colunas de ocorrencia que variam dentro do mesmo id)

| coluna | ids com mais de um valor | exemplos |
|---|---|---|
| data_inversa | 0 | - |
| dia_semana | 0 | - |
| horario | 0 | - |
| uf | 0 | - |
| br | 0 | - |
| km | 0 | - |
| municipio | 0 | - |
| classificacao_acidente | 0 | - |
| fase_dia | 0 | - |
| sentido_via | 0 | - |
| condicao_metereologica | 0 | - |
| tipo_pista | 0 | - |
| tracado_via | 0 | - |
| uso_solo | 0 | - |
| latitude | 0 | - |
| longitude | 0 | - |
| regional | 0 | - |
| delegacia | 0 | - |
| uop | 0 | - |

## 6. Datas

- Em formato ISO `aaaa-mm-dd`: 584010
- Em formato `dd/mm/aaaa`: 0
- Periodo textual: 2025-01-01 a 2025-12-31
- O dicionario descreve data_inversa como dd/mm/aaaa; verificar acima qual formato o arquivo realmente usa.

## 7. Conformidade com o dicionario

- Colunas do dicionario ausentes no arquivo: nenhuma
- Colunas no arquivo fora do dicionario: nenhuma
- Divergencias de grafia entre dicionario e arquivo: `classifica??o_acidente` -> `classificacao_acidente`, `condi??o_meteorologica` -> `condicao_metereologica`

## 8. Panorama por coluna

| coluna | nivel | nao_nulos | nulos | pct_nulos | valores_distintos | formato_invalido | exemplos_formato_invalido | com_espaco_nas_bordas | tokens_texto_de_ausencia |
|---|---|---|---|---|---|---|---|---|---|
| id | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| pesid | pessoa | 527209 | 56801 | 9.726 |  | 0 |  | 0 |  |
| data_inversa | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| dia_semana | ocorrencia | 584010 | 0 | 0.0 | 7 | 0 |  | 0 |  |
| horario | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| uf | ocorrencia | 584010 | 0 | 0.0 | 27 | 0 |  | 0 |  |
| br | ocorrencia | 582566 | 1444 | 0.2473 |  | 0 |  | 0 |  |
| km | ocorrencia | 582566 | 1444 | 0.2473 |  | 0 |  | 0 |  |
| municipio | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| causa_principal | causa | 584010 | 0 | 0.0 | 2 | 0 |  | 0 |  |
| causa_acidente | causa | 584010 | 0 | 0.0 | 70 | 0 |  | 0 |  |
| ordem_tipo_acidente | tipo_evento | 584010 | 0 | 0.0 | 14 | 0 |  | 0 |  |
| tipo_acidente | tipo_evento | 584010 | 0 | 0.0 | 17 | 0 |  | 0 |  |
| classificacao_acidente | ocorrencia | 584003 | 7 | 0.0012 | 4 | 0 |  | 0 |  |
| fase_dia | ocorrencia | 584010 | 0 | 0.0 | 4 | 0 |  | 0 |  |
| sentido_via | ocorrencia | 584010 | 0 | 0.0 | 3 | 0 |  | 0 |  |
| condicao_metereologica | ocorrencia | 584010 | 0 | 0.0 | 9 | 0 |  | 0 | Ignorado=7130 |
| tipo_pista | ocorrencia | 584010 | 0 | 0.0 | 3 | 0 |  | 0 |  |
| tracado_via | ocorrencia | 584010 | 0 | 0.0 | 605 | 0 |  | 0 |  |
| uso_solo | ocorrencia | 584010 | 0 | 0.0 | 2 | 0 |  | 0 |  |
| id_veiculo | veiculo | 565393 | 18617 | 3.1878 |  | 0 |  | 0 |  |
| tipo_veiculo | veiculo | 565393 | 18617 | 3.1878 | 26 | 0 |  | 0 |  |
| marca | veiculo | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| ano_fabricacao_veiculo | veiculo | 565393 | 18617 | 3.1878 |  | 0 |  | 0 |  |
| tipo_envolvido | pessoa | 527209 | 56801 | 9.726 | 6 | 0 |  | 0 |  |
| estado_fisico | pessoa | 527209 | 56801 | 9.726 | 6 | 0 |  | 0 |  |
| idade | pessoa | 478397 | 105613 | 18.0841 |  | 0 |  | 0 |  |
| sexo | pessoa | 527209 | 56801 | 9.726 | 5 | 0 |  | 0 | Ignorado=1171 |
| ilesos | pessoa | 527209 | 56801 | 9.726 | 3 | 0 |  | 0 |  |
| feridos_leves | pessoa | 527209 | 56801 | 9.726 | 3 | 0 |  | 0 |  |
| feridos_graves | pessoa | 527209 | 56801 | 9.726 | 3 | 0 |  | 0 |  |
| mortos | pessoa | 527209 | 56801 | 9.726 | 3 | 0 |  | 0 |  |
| latitude | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| longitude | ocorrencia | 584010 | 0 | 0.0 |  | 0 |  | 0 |  |
| regional | ocorrencia | 583994 | 16 | 0.0027 | 29 | 0 |  | 0 |  |
| delegacia | ocorrencia | 583820 | 190 | 0.0325 |  | 0 |  | 0 |  |
| uop | ocorrencia | 583567 | 443 | 0.0759 |  | 0 |  | 0 |  |

## 9. Categorias observadas

### dia_semana (7 valores distintos)

- `sábado`: 93778
- `domingo`: 93672
- `sexta-feira`: 93659
- `segunda-feira`: 80118
- `quinta-feira`: 76512
- `quarta-feira`: 73941
- `terça-feira`: 72330

### uf (27 valores distintos)

- `MG`: 82397
- `PR`: 70759
- `SC`: 51403
- `RS`: 35952
- `BA`: 33498
- `SP`: 32280
- `RJ`: 31474
- `GO`: 30070
- `MT`: 26891
- `PE`: 25046

### causa_principal (2 valores distintos)

- `Sim`: 346083
- `Não`: 237927

### classificacao_acidente (4 valores distintos)

- `Com Vítimas Feridas`: 435193
- `Com Vítimas Fatais`: 94032
- `Sem Vítimas`: 54778
- `<AUSENTE>`: 7

### fase_dia (4 valores distintos)

- `Pleno dia`: 324063
- `Plena Noite`: 195169
- `Anoitecer`: 33480
- `Amanhecer`: 31298

### sentido_via (3 valores distintos)

- `Crescente`: 316401
- `Decrescente`: 266165
- `Não Informado`: 1444

### condicao_metereologica (9 valores distintos)

- `Céu Claro`: 364421
- `Nublado`: 91831
- `Chuva`: 59783
- `Sol`: 33526
- `Garoa/Chuvisco`: 20603
- `Ignorado`: 7130
- `Nevoeiro/Neblina`: 5364
- `Vento`: 1350
- `Neve`: 2

### tipo_pista (3 valores distintos)

- `Simples`: 319222
- `Dupla`: 216150
- `Múltipla`: 48638

### tracado_via (605 valores distintos)

- `Reta`: 298900
- `Curva`: 59456
- `Reta;Declive`: 21535
- `Reta;Aclive`: 19733
- `Curva;Declive`: 17031
- `Declive;Reta`: 15341
- `Aclive;Reta`: 14960
- `Declive;Curva`: 14399
- `Reta;Interseção de Vias`: 10623
- `Interseção de Vias`: 10378

### uso_solo (2 valores distintos)

- `Não`: 358931
- `Sim`: 225079

### tipo_veiculo (26 valores distintos)

- `Automóvel`: 190205
- `Motocicleta`: 117267
- `Semireboque`: 49862
- `Caminhonete`: 49712
- `Caminhão-trator`: 42868
- `Caminhão`: 34135
- `Ônibus`: 26789
- `<AUSENTE>`: 18617
- `Camioneta`: 13737
- `Motoneta`: 11568

### tipo_envolvido (6 valores distintos)

- `Condutor`: 354002
- `Passageiro`: 154590
- `<AUSENTE>`: 56801
- `Testemunha`: 11166
- `Pedestre`: 7351
- `Cavaleiro`: 100

### estado_fisico (6 valores distintos)

- `Ileso`: 218091
- `Lesões Leves`: 179140
- `Lesões Graves`: 66983
- `<AUSENTE>`: 56801
- `Não Informado`: 35083
- `Óbito`: 27912

### sexo (5 valores distintos)

- `Masculino`: 366839
- `Feminino`: 124116
- `<AUSENTE>`: 56801
- `Não Informado`: 35083
- `Ignorado`: 1171

### ilesos (3 valores distintos)

- `0`: 309118
- `1`: 218091
- `<AUSENTE>`: 56801

### feridos_leves (3 valores distintos)

- `0`: 348069
- `1`: 179140
- `<AUSENTE>`: 56801

### feridos_graves (3 valores distintos)

- `0`: 460226
- `1`: 66983
- `<AUSENTE>`: 56801

### mortos (3 valores distintos)

- `0`: 499297
- `<AUSENTE>`: 56801
- `1`: 27912

### ordem_tipo_acidente (14 valores distintos)

- `1`: 305947
- `2`: 164011
- `3`: 83292
- `4`: 19862
- `5`: 6261
- `6`: 2645
- `7`: 1084
- `8`: 504
- `9`: 282
- `10`: 86

### tipo_acidente (17 valores distintos)

- `Colisão traseira`: 86904
- `Tombamento`: 82415
- `Queda de ocupante de veículo`: 74532
- `Saída de leito carroçável`: 72590
- `Colisão com objeto`: 46252
- `Colisão transversal`: 44627
- `Colisão lateral mesmo sentido`: 42226
- `Colisão frontal`: 39227
- `Capotamento`: 27569
- `Colisão lateral sentido oposto`: 20924

### causa_acidente (70 valores distintos)

- `Reação tardia ou ineficiente do condutor`: 83405
- `Ausência de reação do condutor`: 72798
- `Velocidade Incompatível`: 53646
- `Acessar a via sem observar a presença dos outros veículos`: 41956
- `Condutor deixou de manter distância do veículo da frente`: 40418
- `Manobra de mudança de faixa`: 31360
- `Ingestão de álcool pelo condutor`: 27041
- `Transitar na contramão`: 23072
- `Ultrapassagem Indevida`: 19304
- `Condutor Dormindo`: 17673

### regional (29 valores distintos)

- `SPRF-MG`: 82277
- `SPRF-PR`: 70320
- `SPRF-SC`: 51786
- `SPRF-RS`: 36005
- `SPRF-BA`: 32552
- `SPRF-SP`: 32042
- `SPRF-RJ`: 31474
- `SPRF-MT`: 27306
- `SPRF-PE`: 25842
- `SPRF-GO`: 22368


> Observado no arquivo nao e o mesmo que permitido pelo dicionario. As categorias validas sao fixadas em `config/regras_qualidade.json`.
