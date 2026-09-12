r"""
test_validacao.py - testes do PROPRIO validador.

Por que testar o validador: um verificador que aprova tudo e inutil. Estes testes
criam arquivos SINTETICOS pequenos, isolados dos dados reais da PRF, cada um com um
defeito conhecido, e conferem se o validador reprova pelo motivo certo.

Casos cobertos (pedidos no enunciado):
  1. arquivo valido                       -> aprovado, codigo de saida 0
  2. coluna obrigatoria ausente           -> reprovado (E001)
  3. chave conflitante (id repetido)      -> reprovado (E007)
  4. data impossivel (2025-02-30)         -> reprovado (T201)
  5. categoria invalida                   -> reprovado (C50-tipo_pista)
  6. contagem negativa                    -> reprovado (C40-qtd_mortos)
  7. nulo permitido                       -> continua aprovado
  8. alvo ausente                         -> linha inelegivel, base ainda aprovada
  9. arquivo inexistente / vazio          -> erro operacional, codigo 2
 10. idempotencia da limpeza              -> rodar duas vezes gera bytes identicos

Como rodar:
  python -m pytest tests -v
  python tests\test_validacao.py          (roda sem o pytest instalado)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import validar_dados  # noqa: E402
from comum import ESCRITA_LIMPO  # noqa: E402

DIR_TMP = RAIZ / "tests" / "tmp"

# ---------------------------------------------------------------------------
# Uma ocorrencia FICTICIA valida, montada a partir do esquema confirmado.
# Nao representa dados reais da PRF: os ids comecam com 9 para deixar claro.
# ---------------------------------------------------------------------------
LINHA_BASE = {
    "id": "900001",
    "data_inversa": "2025-03-14",
    "horario": "07:45:00",
    "dia_semana": "Sexta-feira",
    "dia_semana_calculado": "Sexta-feira",
    "dia_semana_divergente": "Não",
    "ano": "2025",
    "mes": "3",
    "mes_nome": "Março",
    "hora": "7",
    "faixa_horaria": "Manhã",
    "fim_de_semana": "Não",
    "uf": "MG",
    "br": "381",
    "km": "120,5",
    "municipio": "BETIM",
    "fase_dia": "Pleno Dia",
    "sentido_via": "Crescente",
    "condicao_metereologica": "Céu Claro",
    "tipo_pista": "Dupla",
    "tracado_via": "Reta",
    "uso_solo": "Urbano",
    "classificacao_acidente": "Com Vítimas Feridas",
    "qtd_pessoas": "3",
    "qtd_ilesos": "1",
    "qtd_feridos_leves": "2",
    "qtd_feridos_graves": "0",
    "qtd_feridos": "2",
    "qtd_mortos": "0",
    "qtd_estado_fisico_nao_informado": "0",
    "qtd_veiculos": "2",
    "qtd_causas_distintas": "1",
    "qtd_tipos_distintos": "1",
    "causa_principal_acidente": "Reação tardia ou ineficiente do condutor",
    "tipo_acidente_principal": "Colisão traseira",
    "latitude": "-19,96777000",
    "longitude": "-44,19833000",
    "regional": "SPRF-MG",
    "delegacia": "DEL01-MG",
    "uop": "UOP01-DEL01-MG",
    "alvo_ausente": "Não",
    "elegivel_modelo": "Sim",
    "motivo_inelegibilidade": "",
    "entradas_ausentes": "",
}


def base_sintetica(n: int = 40) -> pd.DataFrame:
    """Gera n ocorrencias ficticias validas e coerentes entre si.

    O suporte de 40 linhas por classe existe para que a regra M404 (suporte
    minimo de 30) nao falhe nos casos que deveriam passar.
    """
    dias = {
        "2025-03-10": "Segunda-feira", "2025-03-11": "Terça-feira",
        "2025-03-12": "Quarta-feira", "2025-03-13": "Quinta-feira",
        "2025-03-14": "Sexta-feira", "2025-03-15": "Sábado", "2025-03-16": "Domingo",
    }
    datas = list(dias.items())
    perfis = [
        # (classificacao, ilesos, leves, graves, mortos)
        ("Com Vítimas Feridas", 1, 2, 0, 0),
        ("Sem Vítimas", 2, 0, 0, 0),
        ("Com Vítimas Fatais", 0, 0, 1, 1),
    ]
    horas = ["03:10:00", "09:20:00", "14:35:00", "21:05:00"]
    faixas = {"03": "Madrugada", "09": "Manhã", "14": "Tarde", "21": "Noite"}

    linhas = []
    for i in range(n * len(perfis)):
        linha = dict(LINHA_BASE)
        data, dia = datas[i % len(datas)]
        classe, ilesos, leves, graves, mortos = perfis[i % len(perfis)]
        hora = horas[i % len(horas)]
        linha["id"] = str(900001 + i)
        linha["data_inversa"] = data
        linha["dia_semana"] = dia
        linha["dia_semana_calculado"] = dia
        linha["fim_de_semana"] = "Sim" if dia in ("Sábado", "Domingo") else "Não"
        linha["ano"], linha["mes"], linha["mes_nome"] = "2025", "3", "Março"
        linha["horario"] = hora
        linha["hora"] = str(int(hora[:2]))
        linha["faixa_horaria"] = faixas[hora[:2]]
        linha["classificacao_acidente"] = classe
        linha["qtd_ilesos"] = str(ilesos)
        linha["qtd_feridos_leves"] = str(leves)
        linha["qtd_feridos_graves"] = str(graves)
        linha["qtd_feridos"] = str(leves + graves)
        linha["qtd_mortos"] = str(mortos)
        linha["qtd_estado_fisico_nao_informado"] = "0"
        linha["qtd_pessoas"] = str(ilesos + leves + graves + mortos)
        linhas.append(linha)
    return pd.DataFrame(linhas)


def gravar(df: pd.DataFrame, nome: str) -> Path:
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    caminho = DIR_TMP / nome
    df.to_csv(caminho, **ESCRITA_LIMPO)
    return caminho


def validar(caminho: Path) -> tuple[int, dict]:
    """Executa o validador no arquivo e devolve (codigo_de_saida, validacao.json)."""
    saida = DIR_TMP / f"rel_{caminho.stem}"
    codigo = validar_dados.main([
        "--arquivo", str(caminho), "--saida", str(saida),
        "--sem-reconciliacao", "--silencioso",
    ])
    relatorio = json.loads((saida / "validacao.json").read_text(encoding="utf-8"))
    return codigo, relatorio


def status_da_regra(relatorio: dict, identificador: str) -> str:
    for r in relatorio["regras"]:
        if r["id"] == identificador:
            return r["status"]
    return "REGRA_INEXISTENTE"


# ---------------------------------------------------------------------------
# 1. Arquivo valido precisa ser aprovado.
# ---------------------------------------------------------------------------
def test_arquivo_valido_e_aprovado():
    caminho = gravar(base_sintetica(), "caso01_valido.csv")
    codigo, rel = validar(caminho)
    assert rel["status_global"] in ("APROVADA", "APROVADA_COM_RESSALVAS"), rel["resumo"]
    assert codigo == 0
    assert rel["resumo"]["criticas_falhadas"] == []
    assert rel["resumo"]["criticas_nao_verificadas"] == []


# ---------------------------------------------------------------------------
# 2. Coluna obrigatoria ausente precisa reprovar.
# ---------------------------------------------------------------------------
def test_coluna_obrigatoria_ausente_reprova():
    df = base_sintetica().drop(columns=["tipo_pista"])
    codigo, rel = validar(gravar(df, "caso02_sem_coluna.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "E001") == "FALHOU"


# ---------------------------------------------------------------------------
# 3. Chave conflitante: dois registros com o mesmo id.
# ---------------------------------------------------------------------------
def test_chave_duplicada_reprova():
    df = base_sintetica()
    df.loc[1, "id"] = df.loc[0, "id"]
    codigo, rel = validar(gravar(df, "caso03_chave_duplicada.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "E007") == "FALHOU"


# ---------------------------------------------------------------------------
# 4. Data impossivel: 30 de fevereiro nao existe.
# ---------------------------------------------------------------------------
def test_data_impossivel_reprova():
    df = base_sintetica()
    df.loc[0, "data_inversa"] = "2025-02-30"
    codigo, rel = validar(gravar(df, "caso04_data_impossivel.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "T201") == "FALHOU"


def test_data_fora_do_formato_canonico_reprova():
    df = base_sintetica()
    df.loc[0, "data_inversa"] = "14/03/2025"
    codigo, rel = validar(gravar(df, "caso04b_data_formato.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "T201") == "FALHOU"


# ---------------------------------------------------------------------------
# 5. Categoria fora do dominio do contrato.
# ---------------------------------------------------------------------------
def test_categoria_invalida_reprova():
    df = base_sintetica()
    df.loc[0, "tipo_pista"] = "Tripla"
    codigo, rel = validar(gravar(df, "caso05_categoria_invalida.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "C50-tipo_pista") == "FALHOU"


def test_tracado_fora_de_ordem_gera_ressalva():
    """tracado_via desordenado e aviso, nao critico: nao deve reprovar."""
    df = base_sintetica()
    df.loc[0, "tracado_via"] = "Reta;Declive"
    codigo, rel = validar(gravar(df, "caso05b_tracado_desordenado.csv"))
    assert status_da_regra(rel, "C52-tracado_via") == "FALHOU"
    assert rel["status_global"] == "APROVADA_COM_RESSALVAS"
    assert codigo == 0


# ---------------------------------------------------------------------------
# 6. Contagem negativa: nao existe "-1 morto".
# ---------------------------------------------------------------------------
def test_contagem_negativa_reprova():
    df = base_sintetica()
    df.loc[0, "qtd_mortos"] = "-1"
    codigo, rel = validar(gravar(df, "caso06_contagem_negativa.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "C40-qtd_mortos") == "FALHOU"


def test_inteiro_com_parte_fracionaria_reprova():
    df = base_sintetica()
    df.loc[0, "qtd_pessoas"] = "3,0"
    codigo, rel = validar(gravar(df, "caso06b_inteiro_fracionario.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "C30-qtd_pessoas") == "FALHOU"


# ---------------------------------------------------------------------------
# 7. Nulo PERMITIDO nao pode reprovar.
# ---------------------------------------------------------------------------
def test_nulo_permitido_nao_reprova():
    df = base_sintetica()
    df.loc[0, "br"] = ""          # nulo_permitido = true
    df.loc[0, "km"] = ""          # nulo_permitido = true
    df.loc[0, "sentido_via"] = ""  # nulo_permitido = true
    codigo, rel = validar(gravar(df, "caso07_nulo_permitido.csv"))
    assert rel["resumo"]["criticas_falhadas"] == []
    assert codigo == 0


def test_nulo_proibido_reprova():
    df = base_sintetica()
    df.loc[0, "uso_solo"] = ""    # nulo_permitido = false, severidade critico
    codigo, rel = validar(gravar(df, "caso07b_nulo_proibido.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "C10-uso_solo") == "FALHOU"


# ---------------------------------------------------------------------------
# 8. Alvo ausente: linha continua na base, mas fica inelegivel.
# ---------------------------------------------------------------------------
def test_alvo_ausente_torna_linha_inelegivel():
    df = base_sintetica()
    df.loc[0, "classificacao_acidente"] = ""
    df.loc[0, "alvo_ausente"] = "Sim"
    df.loc[0, "elegivel_modelo"] = "Não"
    df.loc[0, "motivo_inelegibilidade"] = "classificacao_acidente ausente"
    # As contagens de vitimas continuam validas: o alvo nao foi imputado.
    codigo, rel = validar(gravar(df, "caso08_alvo_ausente.csv"))
    assert rel["resumo"]["criticas_falhadas"] == []
    assert codigo == 0
    assert status_da_regra(rel, "X310") == "PASSOU"
    assert status_da_regra(rel, "X311") == "PASSOU"


def test_alvo_ausente_com_sinalizador_errado_reprova():
    """Se o alvo esta vazio mas alvo_ausente diz 'Nao', a regra R10 deve pegar."""
    df = base_sintetica()
    df.loc[0, "classificacao_acidente"] = ""
    df.loc[0, "alvo_ausente"] = "Não"
    codigo, rel = validar(gravar(df, "caso08b_sinalizador_errado.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "X310") == "FALHOU"


def test_motivo_em_linha_elegivel_reprova():
    """A coluna de motivo nao pode ser usada como campo de observacao (regra R16)."""
    df = base_sintetica()
    df.loc[0, "motivo_inelegibilidade"] = "condicao_metereologica ausente"
    codigo, rel = validar(gravar(df, "caso08d_motivo_em_linha_elegivel.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "X316") == "FALHOU"


def test_gravidade_incoerente_com_contagens_reprova():
    """'Sem Vitimas' com morto contradiz o dicionario: regra R03."""
    df = base_sintetica()
    df.loc[1, "classificacao_acidente"] = "Sem Vítimas"
    df.loc[1, "qtd_mortos"] = "1"
    df.loc[1, "qtd_ilesos"] = "1"
    df.loc[1, "qtd_feridos_leves"] = "0"
    df.loc[1, "qtd_feridos_graves"] = "0"
    df.loc[1, "qtd_feridos"] = "0"
    df.loc[1, "qtd_pessoas"] = "2"
    codigo, rel = validar(gravar(df, "caso08c_gravidade_incoerente.csv"))
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "X303") == "FALHOU"


# ---------------------------------------------------------------------------
# 9. Erros operacionais devolvem codigo 2, nao 1.
# ---------------------------------------------------------------------------
def test_arquivo_inexistente_devolve_codigo_2():
    codigo = validar_dados.main([
        "--arquivo", str(DIR_TMP / "nao_existe.csv"),
        "--saida", str(DIR_TMP / "rel_inexistente"),
        "--sem-reconciliacao", "--silencioso",
    ])
    assert codigo == 2


def test_arquivo_vazio_devolve_codigo_2():
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    vazio = DIR_TMP / "caso09_vazio.csv"
    vazio.write_bytes(b"")
    codigo = validar_dados.main([
        "--arquivo", str(vazio), "--saida", str(DIR_TMP / "rel_vazio"),
        "--sem-reconciliacao", "--silencioso",
    ])
    assert codigo == 2


# ---------------------------------------------------------------------------
# 10. Indice exportado por acidente deve ser detectado.
# ---------------------------------------------------------------------------
def test_indice_exportado_reprova():
    df = base_sintetica()
    caminho = DIR_TMP / "caso10_com_indice.csv"
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, sep=";", encoding="utf-8-sig", decimal=",", index=True)
    codigo, rel = validar(caminho)
    assert rel["status_global"] == "REPROVADA"
    assert codigo == 1
    assert status_da_regra(rel, "E003") == "FALHOU"


# ---------------------------------------------------------------------------
# 11. Idempotencia: limpar duas vezes precisa dar exatamente o mesmo arquivo.
# ---------------------------------------------------------------------------
def test_limpeza_e_idempotente():
    """Roda a limpeza duas vezes sobre a mesma amostra e compara byte a byte.

    Isso prova que a limpeza e deterministica: nao muda valores nem a ordem dos
    registros a cada execucao. Usa --base-saida para nao tocar nos arquivos reais.
    """
    entrada = RAIZ / "data" / "raw" / "acidentes2025_todas_causas_tipos.csv"
    if not entrada.exists():
        print("AVISO: base bruta ausente, teste de idempotencia NAO EXECUTADO")
        return

    saidas = []
    for rodada in ("run1", "run2"):
        destino = DIR_TMP / rodada
        codigo = subprocess.run(
            [sys.executable, str(RAIZ / "src" / "limpeza.py"),
             "--entrada", str(entrada), "--amostra", "30000",
             "--base-saida", str(destino)],
            capture_output=True, text=True,
        ).returncode
        assert codigo == 0, "a limpeza falhou durante o teste de idempotencia"
        saidas.append((destino / "processed" / "prf_limpo.csv").read_bytes())

    assert saidas[0] == saidas[1], "a segunda limpeza produziu um arquivo diferente"

    # Confere tambem que a ordem dos ids e estavel e crescente.
    d = pd.read_csv(DIR_TMP / "run1" / "processed" / "prf_limpo.csv",
                    sep=";", encoding="utf-8-sig", dtype=str)
    ids = pd.to_numeric(d["id"])
    assert ids.is_monotonic_increasing, "a ordem dos registros nao e estavel"


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print(f"[OK]    {teste.__name__}")
        except AssertionError as erro:
            falhas += 1
            print(f"[FALHOU] {teste.__name__}: {erro}")
        except Exception as erro:  # erro inesperado no proprio teste
            falhas += 1
            print(f"[ERRO]  {teste.__name__}: {type(erro).__name__}: {erro}")
    print(f"\n{len(testes) - falhas} de {len(testes)} testes passaram.")
    sys.exit(1 if falhas else 0)
