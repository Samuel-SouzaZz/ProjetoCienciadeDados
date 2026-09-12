# Relatorio de validacao da base limpa

**STATUS GLOBAL: APROVADA_COM_RESSALVAS**

- Arquivo validado: `C:\Users\Administrator\Desktop\Ciencia de dados\data\processed\prf_limpo.csv`
- SHA-256: `0a028fe02ec748e115ab5e4d0d4d3cda3b6ae034a5b26deaebc69d267fa3d4ed`
- Linhas x colunas: 72529 x 44
- Contrato: `C:\Users\Administrator\Desktop\Ciencia de dados\config\regras_qualidade.json` versao 1.0.0 (2026-09-12)
- Data da execucao: 2026-09-12T14:41:27-03:00
- Versoes: Python 3.12.6, pandas 2.2.3, scikit-learn 1.6.1

## Resumo

- Regras avaliadas: 177
- Por status: {'PASSOU': 175, 'FALHOU': 2}
- Criticas que falharam: nenhuma
- Criticas nao verificadas: nenhuma

### Ressalvas

- [X312] km preenchido deve ser >= 0,1 conforme o dicionario. - 175 violacao(oes) (0.241283%)
- [X313] qtd_veiculos deve ser >= 1. - 5 violacao(oes) (0.006894%)

## Tres coisas diferentes

- **qualidade_da_base**: conformidade com as regras explicitas deste contrato
- **elegibilidade_para_treino**: ter alvo preenchido (regras M402/M403)
- **suficiencia_de_amostra**: suporte por classe (regra M404); uma base integra pode ser insuficiente para modelar

## Regras avaliadas

| id | descricao | severidade | status | linhas_avaliadas | violacoes | pct_violacoes |
|---|---|---|---|---|---|---|
| E001 | Todas as colunas declaradas no contrato estao presentes. | critico | PASSOU | 44 | 0 | 0.0 |
| E002 | Nomes de coluna sao unicos. | critico | PASSOU | 44 | 0 | 0.0 |
| E003 | Nenhuma coluna de indice foi exportada por acidente. | critico | PASSOU | 44 | 0 | 0.0 |
| E004 | Nenhuma coluna fora do contrato. | aviso | PASSOU | 44 | 0 | 0.0 |
| E005 | O arquivo tem ao menos uma linha de dados. | critico | PASSOU | 72529 | 0 | 0.0 |
| E006 | Chave primaria ['id'] preenchida em todas as linhas. | critico | PASSOU | 72529 | 0 | 0.0 |
| E007 | Chave primaria ['id'] e unica. | critico | PASSOU | 72529 | 0 | 0.0 |
| E008 | Nenhuma linha e integralmente duplicada. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-id | 'id' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-id | 'id' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C20-id | 'id' respeita o padrao ^[0-9]+$. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-data_inversa | 'data_inversa' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-data_inversa | 'data_inversa' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C20-data_inversa | 'data_inversa' respeita o padrao ^[0-9]{4}-[0-9]{2}-[0-9]{2}$. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-horario | 'horario' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-horario | 'horario' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C20-horario | 'horario' respeita o padrao ^([01][0-9]\|2[0-3]):[0-5][0-9]:[0-5][0-9]$. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-dia_semana | 'dia_semana' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-dia_semana | 'dia_semana' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-dia_semana | 'dia_semana' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-uf | 'uf' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-uf | 'uf' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C20-uf | 'uf' respeita o padrao ^[A-Z]{2}$. | critico | PASSOU | 72529 | 0 | 0.0 |
| C50-uf | 'uf' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-br | 'br' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 167 | 0.230253 |
| C11-br | 'br' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-br | 'br' e inteiro, sem parte fracionaria. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-br | 'br' dentro de [1, 999]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-km | 'km' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 167 | 0.230253 |
| C11-km | 'km' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-km | 'km' e decimal com virgula como separador. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-km | 'km' dentro de [0.0, 2000.0]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-municipio | 'municipio' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-municipio | 'municipio' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-classificacao_acidente | 'classificacao_acidente' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 1 | 0.001379 |
| C11-classificacao_acidente | 'classificacao_acidente' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-classificacao_acidente | 'classificacao_acidente' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-fase_dia | 'fase_dia' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 0 | 0.0 |
| C11-fase_dia | 'fase_dia' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-fase_dia | 'fase_dia' usa apenas as categorias do contrato. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-sentido_via | 'sentido_via' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 167 | 0.230253 |
| C11-sentido_via | 'sentido_via' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-sentido_via | 'sentido_via' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-condicao_metereologica | 'condicao_metereologica' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 1000 | 1.378759 |
| C11-condicao_metereologica | 'condicao_metereologica' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-condicao_metereologica | 'condicao_metereologica' usa apenas as categorias do contrato. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-tipo_pista | 'tipo_pista' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-tipo_pista | 'tipo_pista' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-tipo_pista | 'tipo_pista' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-tracado_via | 'tracado_via' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-tracado_via | 'tracado_via' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C51-tracado_via | 'tracado_via' usa apenas componentes permitidos. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C52-tracado_via | 'tracado_via' tem componentes em ordem alfabetica e sem repeticao. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-uso_solo | 'uso_solo' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-uso_solo | 'uso_solo' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-uso_solo | 'uso_solo' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-latitude | 'latitude' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 0 | 0.0 |
| C11-latitude | 'latitude' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-latitude | 'latitude' e decimal com virgula como separador. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-latitude | 'latitude' dentro de [-34.0, 6.0]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-longitude | 'longitude' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 0 | 0.0 |
| C11-longitude | 'longitude' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-longitude | 'longitude' e decimal com virgula como separador. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-longitude | 'longitude' dentro de [-75.0, -32.0]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-regional | 'regional' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 2 | 0.002758 |
| C11-regional | 'regional' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-delegacia | 'delegacia' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 22 | 0.030333 |
| C11-delegacia | 'delegacia' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-uop | 'uop' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 38 | 0.052393 |
| C11-uop | 'uop' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-ano | 'ano' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-ano | 'ano' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-ano | 'ano' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-ano | 'ano' dentro de [2017, 2100]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-mes | 'mes' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-mes | 'mes' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-mes | 'mes' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-mes | 'mes' dentro de [1, 12]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-mes_nome | 'mes_nome' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-mes_nome | 'mes_nome' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-mes_nome | 'mes_nome' usa apenas as categorias do contrato. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-hora | 'hora' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-hora | 'hora' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-hora | 'hora' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-hora | 'hora' dentro de [0, 23]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-faixa_horaria | 'faixa_horaria' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-faixa_horaria | 'faixa_horaria' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-faixa_horaria | 'faixa_horaria' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-fim_de_semana | 'fim_de_semana' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-fim_de_semana | 'fim_de_semana' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-fim_de_semana | 'fim_de_semana' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-dia_semana_calculado | 'dia_semana_calculado' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-dia_semana_calculado | 'dia_semana_calculado' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-dia_semana_calculado | 'dia_semana_calculado' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-dia_semana_divergente | 'dia_semana_divergente' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-dia_semana_divergente | 'dia_semana_divergente' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-dia_semana_divergente | 'dia_semana_divergente' usa apenas as categorias do contrato. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_pessoas | 'qtd_pessoas' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_pessoas | 'qtd_pessoas' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_pessoas | 'qtd_pessoas' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_pessoas | 'qtd_pessoas' dentro de [1, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_ilesos | 'qtd_ilesos' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_ilesos | 'qtd_ilesos' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_ilesos | 'qtd_ilesos' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_ilesos | 'qtd_ilesos' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_feridos_leves | 'qtd_feridos_leves' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_feridos_leves | 'qtd_feridos_leves' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_feridos_leves | 'qtd_feridos_leves' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_feridos_leves | 'qtd_feridos_leves' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_feridos_graves | 'qtd_feridos_graves' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_feridos_graves | 'qtd_feridos_graves' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_feridos_graves | 'qtd_feridos_graves' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_feridos_graves | 'qtd_feridos_graves' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_feridos | 'qtd_feridos' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_feridos | 'qtd_feridos' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_feridos | 'qtd_feridos' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_feridos | 'qtd_feridos' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_mortos | 'qtd_mortos' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_mortos | 'qtd_mortos' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_mortos | 'qtd_mortos' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_mortos | 'qtd_mortos' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_estado_fisico_nao_informado | 'qtd_estado_fisico_nao_informado' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_estado_fisico_nao_informado | 'qtd_estado_fisico_nao_informado' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_estado_fisico_nao_informado | 'qtd_estado_fisico_nao_informado' e inteiro, sem parte fracionaria. | critico | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_estado_fisico_nao_informado | 'qtd_estado_fisico_nao_informado' dentro de [0, None]. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_veiculos | 'qtd_veiculos' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_veiculos | 'qtd_veiculos' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_veiculos | 'qtd_veiculos' e inteiro, sem parte fracionaria. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_veiculos | 'qtd_veiculos' dentro de [0, None]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_causas_distintas | 'qtd_causas_distintas' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_causas_distintas | 'qtd_causas_distintas' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_causas_distintas | 'qtd_causas_distintas' e inteiro, sem parte fracionaria. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_causas_distintas | 'qtd_causas_distintas' dentro de [1, None]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-qtd_tipos_distintos | 'qtd_tipos_distintos' nao pode ficar vazia. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C11-qtd_tipos_distintos | 'qtd_tipos_distintos' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C30-qtd_tipos_distintos | 'qtd_tipos_distintos' e inteiro, sem parte fracionaria. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C40-qtd_tipos_distintos | 'qtd_tipos_distintos' dentro de [1, None]. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-causa_principal_acidente | 'causa_principal_acidente' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 0 | 0.0 |
| C11-causa_principal_acidente | 'causa_principal_acidente' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-tipo_acidente_principal | 'tipo_acidente_principal' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 0 | 0.0 |
| C11-tipo_acidente_principal | 'tipo_acidente_principal' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-alvo_ausente | 'alvo_ausente' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-alvo_ausente | 'alvo_ausente' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-alvo_ausente | 'alvo_ausente' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-elegivel_modelo | 'elegivel_modelo' nao pode ficar vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| C11-elegivel_modelo | 'elegivel_modelo' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C50-elegivel_modelo | 'elegivel_modelo' usa apenas as categorias do contrato. | critico | PASSOU | 72529 | 0 | 0.0 |
| C10-motivo_inelegibilidade | 'motivo_inelegibilidade' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 72528 | 99.998621 |
| C11-motivo_inelegibilidade | 'motivo_inelegibilidade' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| C10-entradas_ausentes | 'entradas_ausentes' aceita ausencia (politica do contrato). | informativo | PASSOU | 72529 | 71529 | 98.621241 |
| C11-entradas_ausentes | 'entradas_ausentes' sem espaco no inicio ou no fim. | aviso | PASSOU | 72529 | 0 | 0.0 |
| T201 | data_inversa e uma data real no formato canonico aaaa-mm-dd. | critico | PASSOU | 72529 | 0 | 0.0 |
| T202 | data_inversa dentro do periodo declarado ['2025-01-01', '2025-12-31']. | critico | PASSOU | 72529 | 0 | 0.0 |
| T203 | data_inversa nao esta no futuro. | aviso | PASSOU | 72529 | 0 | 0.0 |
| T204 | horario e hora possivel no formato canonico HH:MM:SS. | critico | PASSOU | 72529 | 0 | 0.0 |
| X301 | qtd_pessoas deve ser igual a soma de ilesos, feridos leves, feridos graves, mortos e estado fisico nao informado. | critico | PASSOU | 72529 | 0 | 0.0 |
| X302 | qtd_feridos deve ser igual a qtd_feridos_leves + qtd_feridos_graves. | critico | PASSOU | 72529 | 0 | 0.0 |
| X303 | Quando classificacao_acidente = 'Sem Vitimas', qtd_feridos e qtd_mortos devem ser 0. | critico | PASSOU | 72529 | 0 | 0.0 |
| X304 | Quando classificacao_acidente = 'Com Vitimas Fatais', qtd_mortos deve ser >= 1. | critico | PASSOU | 72529 | 0 | 0.0 |
| X305 | Quando classificacao_acidente = 'Com Vitimas Feridas', qtd_feridos deve ser >= 1 e qtd_mortos deve ser 0. | critico | PASSOU | 72529 | 0 | 0.0 |
| X306 | fim_de_semana = 'Sim' exatamente quando dia_semana_calculado e Sabado ou Domingo. | critico | PASSOU | 72529 | 0 | 0.0 |
| X307 | ano e mes devem corresponder a data_inversa. | critico | PASSOU | 72529 | 0 | 0.0 |
| X309 | dia_semana_calculado deve corresponder ao dia da semana de data_inversa. | critico | PASSOU | 72529 | 0 | 0.0 |
| X308a | hora corresponde a hora cheia de horario. | critico | PASSOU | 72529 | 0 | 0.0 |
| X308b | faixa_horaria respeita os limites do contrato ({'Madrugada': '00:00:00 a 05:59:59', 'Manha': '06:00:00 a 11:59:59', 'Tarde': '12:00:00 a 17:59:59', 'Noite': '18:00:00 a 23:59:59'}). | critico | PASSOU | 72529 | 0 | 0.0 |
| X310 | alvo_ausente = 'Sim' exatamente quando classificacao_acidente esta vazia. | critico | PASSOU | 72529 | 0 | 0.0 |
| X311 | elegivel_modelo deve ser 'Nao' sempre que alvo_ausente = 'Sim'. | critico | PASSOU | 72529 | 0 | 0.0 |
| X312 | km preenchido deve ser >= 0,1 conforme o dicionario. | aviso | FALHOU | 72529 | 175 | 0.241283 |
| X313 | qtd_veiculos deve ser >= 1. | aviso | FALHOU | 72529 | 5 | 0.006894 |
| X314 | latitude e longitude devem estar dentro dos limites do territorio brasileiro. | aviso | PASSOU | 72529 | 0 | 0.0 |
| X316 | motivo_inelegibilidade esta preenchido exatamente quando elegivel_modelo = 'Nao'. | critico | PASSOU | 72529 | 0 | 0.0 |
| X315 | Nenhuma celula textual deve comecar ou terminar com espaco. | aviso | PASSOU | 3191276 | 0 | 0.0 |
| M401 | Reconciliacao: entrada = duplicatas + quarentena + mantidas, e o numero de ocorrencias declarado corresponde as linhas do CSV. | critico | PASSOU | 584010 | 0 | 0.0 |
| M402 | elegivel_modelo usa apenas Sim/Nao. | critico | PASSOU | 72529 | 0 | 0.0 |
| M403 | Ha registros elegiveis para o treino supervisionado. | critico | PASSOU | 72529 | 0 | 0.0 |
| M404 | Cada classe do alvo tem suporte minimo de 30 registros elegiveis. | aviso | PASSOU | 72528 | 0 | 0.0 |
| M405 | Distribuicao das classes entre os registros elegiveis. | informativo | PASSOU | 72528 | 0 | 0.0 |

## Evidencias das regras que nao passaram

### X312 (aviso / FALHOU)

km preenchido deve ser >= 0,1 conforme o dicionario.

- Violacoes: 175 de 72529 (0.241283%)
- Detalhe: valores preservados de proposito: o dicionario nao da regra de correcao
- Exemplos: {'id': '653391', 'km': '0,0'} | {'id': '654575', 'km': '0,0'} | {'id': '654713', 'km': '0,0'} | {'id': '655956', 'km': '0,0'} | {'id': '656665', 'km': '0,0'}

### X313 (aviso / FALHOU)

qtd_veiculos deve ser >= 1.

- Violacoes: 5 de 72529 (0.006894%)
- Exemplos: {'id': '663131', 'qtd_veiculos': '0'} | {'id': '705149', 'qtd_veiculos': '0'} | {'id': '708496', 'qtd_veiculos': '0'} | {'id': '720196', 'qtd_veiculos': '0'} | {'id': '726474', 'qtd_veiculos': '0'}

## Regras ainda nao confirmadas pelo dicionario

- O dicionario nao fecha a lista de condicao_metereologica; 'Sol' e 'Ceu Claro' coexistem no arquivo e NAO foram unificados.
- O dicionario nao enumera os valores de tracado_via nem documenta que o campo e multivalorado com ';'.
- O dicionario nao enumera fase_dia de forma fechada.
- O dicionario nao explica por que ano_fabricacao_veiculo aparece como 0 nem por que marca aparece como 'NA/NA'.
- O dicionario declara km minimo de 0,1 mas o arquivo traz valores 0; nao ha regra oficial de correcao, por isso os valores foram preservados e apenas sinalizados.
- O dicionario nao define limite superior de idade; o limite de 120 anos usado na revisao de campos e uma decisao deste projeto, registrada em auditoria.

## Limitacoes desta auditoria

- A validacao confere conformidade com estas regras explicitas; nao confere se o registro policial descreve corretamente o mundo real.
- Ausencia de nulos nao significa base correta.
- Frequencias de acidentes nao medem risco por viagem, pois nao ha dados de exposicao ao transito.
- A base limpa cobre apenas o periodo do arquivo fornecido.

> Aprovacao significa conformidade com as regras escritas no contrato. Nao significa que a base esteja '100% limpa', e ausencia de nulos nao e prova de qualidade.
