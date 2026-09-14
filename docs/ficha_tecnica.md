# Ficha técnica

Campos com **[a preencher]** ainda precisam do grupo. Os números técnicos abaixo
vieram das execuções em `reports/` — não inventamos nada.

## Identificação do trabalho

| campo | valor |
|---|---|
| Tema | KDD na base de acidentes da Polícia Rodoviária Federal |
| Pergunta de pesquisa | Quais características temporais, ambientais e estruturais estão associadas à gravidade dos acidentes registrados em rodovias federais? |
| Disciplina | **[a preencher]** |
| Professor(a) | **[a preencher]** |
| Curso | **[a preencher]** |
| Semestre | **[a preencher]** |
| Instituição | **[a preencher]** |
| Data de entrega | **[a preencher]** |
| Data da gravação | **[a preencher]** |

## Grupo

| # | nome | o que fez |
|---|---|---|
| 1 | Samuel Souza | roteiro, design e documentação |
| 2 | Junior Oliveira | roteiro, montagem e organização dos slides |
| 3 | Liandra Rodrigues | apresentação e edição dos slides |
| 4 | Karolline Oliveira | apresentação dos slides |
| 5 | Matheus Oliveira | apresentação dos slides |

## Produção do vídeo

| campo | valor |
|---|---|
| Ferramenta de gravação | **[a preencher]** |
| Ferramenta de edição | **[a preencher]** |
| Duração | **[a preencher]** |
| Formato/resolução | **[a preencher]** |
| Link do vídeo | **[a preencher]** |
| Link do repositório | https://github.com/Samuel-SouzaZz/ProjetoCienciadeDados |

## Fontes de dados utilizadas

| item | valor |
|---|---|
| Base | `acidentes2025_todas_causas_tipos.csv` (agregado por pessoa, com todas as causas e tipos) |
| Origem | arquivo da atividade (Google Drive), dados abertos da PRF |
| Tamanho | 223.019.483 bytes |
| Linhas × colunas | 584.010 × 37 |
| Período | 2025-01-01 a 2025-12-31 |
| Dicionário | `dicionario_acidentes_prf.pdf` — variáveis do BAT a partir de 2017 |
| Portal | https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf |
| Dicionários oficiais | https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes |

## Ambiente técnico

| item | versão |
|---|---|
| Sistema | Windows 10 (10.0.19045) |
| Python | 3.12.6 |
| pandas | 2.2.3 |
| scikit-learn | 1.6.1 |
| matplotlib | 3.10.1 |
| seaborn | 0.13.2 |
| Contrato de qualidade | 1.0.0 |

As versões de cada execução ficam no campo `ambiente` dos `reports/*.json`.

## Resultados da execução

| item | valor |
|---|---|
| Ocorrências na base limpa | 72.529 |
| Pessoas distintas | 177.479 |
| Regras de qualidade | 177 |
| Status da validação | APROVADA_COM_RESSALVAS |
| Testes do validador | 19 de 19 |
| Registros em quarentena | 0 |
| Campos para revisão | 432 |

## Integridade

- Números citados nos documentos vêm de `reports/`, de execução real.
- Os registros F01–F05 da tabela Antes × Depois são fictícios e estão marcados assim;
  não entram em gráfico, treino nem métrica.
- `data/raw/` não foi alterado.
- O resultado do modelo aparece como está, inclusive quando empatou com o chute
  na classe majoritária.
