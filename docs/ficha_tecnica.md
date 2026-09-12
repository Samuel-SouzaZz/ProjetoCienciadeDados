# Ficha técnica

> Modelo para preencher. Os campos marcados como **[a preencher]** não foram
> informados e **não** devem ser inventados.

## Identificação do trabalho

| campo | valor |
|---|---|
| Tema | Aplicação do processo KDD à base de acidentes da Polícia Rodoviária Federal |
| Pergunta de pesquisa | Quais características temporais, ambientais e estruturais estão associadas à gravidade dos acidentes registrados em rodovias federais? |
| Disciplina | **[a preencher]** |
| Professor(a) | **[a preencher]** |
| Curso | **[a preencher]** (ex.: Análise e Desenvolvimento de Sistemas) |
| Semestre | **[a preencher]** |
| Instituição | **[a preencher]** |
| Data de entrega | **[a preencher]** |
| Data da gravação | **[a preencher]** |

## Grupo

| # | nome completo | função no trabalho | slides sob responsabilidade |
|---|---|---|---|
| 1 | **[a preencher]** | Abertura e definição do problema | 1, 2, 3, 4 |
| 2 | **[a preencher]** | Processo KDD e apresentação da base | 5, 6, 7 |
| 3 | **[a preencher]** | Seleção e descarte de atributos | 8, 9 |
| 4 | **[a preencher]** | Pré-processamento e validação | 10, 11, 12 |
| 5 | **[a preencher]** | Transformação e mineração | 13, 14, 15, 16 |
| todos | — | Resultados, aplicação social e encerramento | 17, 18, 19, 20 |

> Ajuste a quantidade de linhas ao tamanho real do grupo. A divisão acima distribui
> as falas de forma equilibrada e mantém todos participando do encerramento, mas não
> pressupõe número de integrantes nem duração exigida.

## Produção do vídeo

| campo | valor |
|---|---|
| Ferramenta de gravação | **[a preencher]** |
| Ferramenta de edição | **[a preencher]** |
| Duração | **[a preencher — não há duração assumida por este documento]** |
| Formato/resolução | **[a preencher]** |
| Link do vídeo | **[a preencher]** |
| Link do repositório/pasta do projeto | **[a preencher]** |

## Fontes de dados utilizadas

| item | valor |
|---|---|
| Base | `acidentes2025_todas_causas_tipos.csv` (dados agregados por pessoa, com todas as causas e tipos) |
| Origem da base | arquivo fornecido pela atividade (Google Drive), correspondente aos dados abertos da PRF |
| Tamanho | 223.019.483 bytes |
| Linhas × colunas | 584.010 × 37 |
| Período coberto | 2025-01-01 a 2025-12-31 |
| Dicionário | `dicionario_acidentes_prf.pdf` — Dicionário de variáveis, dados do BAT a partir de 2017 |
| Portal oficial | https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf |
| Dicionários oficiais | https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes |

## Ambiente técnico da execução

| item | versão |
|---|---|
| Sistema | Windows 10 (10.0.19045) |
| Python | 3.12.6 |
| pandas | 2.2.3 |
| scikit-learn | 1.6.1 |
| matplotlib | 3.10.1 |
| seaborn | 0.13.2 |
| Contrato de qualidade | versão 1.0.0 |

> As versões exatas de cada execução ficam registradas no campo `ambiente` dos
> arquivos `reports/*.json`.

## Resultados verificáveis da execução

| item | valor |
|---|---|
| Ocorrências na base limpa | 72.529 |
| Pessoas distintas | 177.479 |
| Regras de qualidade avaliadas | 177 |
| Status da validação | APROVADA_COM_RESSALVAS |
| Testes do validador | 19 de 19 aprovados |
| Registros em quarentena | 0 |
| Campos enviados para revisão | 432 |

## Declaração de integridade

- Nenhum resultado foi inventado. Todos os números citados nos documentos vêm dos
  arquivos em `reports/`, gerados por execução real.
- Os registros F01–F05 da tabela Antes × Depois são fictícios e estão identificados
  como tal; não entram em gráficos, treinamento ou métricas.
- Os dados originais em `data/raw/` foram preservados sem alteração.
- O resultado do modelo é reportado como está, inclusive quando não supera a
  referência.
