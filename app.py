import csv
import hashlib
import hmac
import io
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from atividade_pratica import atividade_pratica

st.set_page_config(page_title="Bioestatística | Escolha do teste", page_icon="📊", layout="centered")

QUESTOES = [
    {
        "id": 1, "tipo": "unica",
        "texto": "Um pesquisador mede a pressão arterial de 25 pacientes antes e depois de um programa de exercícios físicos. A variável é quantitativa e a distribuição das diferenças entre as duas medidas é aproximadamente normal. Qual teste é mais adequado para verificar uma mudança na média?",
        "opcoes": ["Teste t para amostras independentes", "Teste t pareado", "Teste de Mann–Whitney", "Teste de Wilcoxon para postos sinalizados"],
        "corretas": [1],
        "explicacao": "As medidas pertencem aos mesmos pacientes. O teste t pareado avalia se a média das diferenças intrapessoais difere de zero; a normalidade relevante é a das diferenças."
    },
    {
        "id": 2, "tipo": "unica",
        "texto": "Dois grupos de participantes, um com 30 jovens e outro com 30 idosos, realizam um teste de velocidade de caminhada. Os participantes são diferentes entre os grupos, os valores são aproximadamente normais em cada grupo e as variâncias são semelhantes. O objetivo é comparar as médias. Qual teste escolher?",
        "opcoes": ["Teste de Wilcoxon para postos sinalizados", "Teste t pareado", "Teste t de amostras independentes", "Teste de Mann–Whitney"],
        "corretas": [2],
        "explicacao": "Os grupos são independentes, e o objetivo é comparar as médias. Com as condições informadas, o teste t para amostras independentes é apropriado."
    },
    {
        "id": 3, "tipo": "unica",
        "texto": "Um estudo avalia o escore de dor, de 0 a 10, nos mesmos 18 pacientes antes e depois de uma intervenção. Os dados são tratados como ordinais, e o pesquisador quer verificar uma mudança sistemática nos escores utilizando as diferenças dentro de cada paciente. Qual teste é mais adequado?",
        "opcoes": ["Teste t pareado", "Teste de Mann–Whitney", "Teste t para amostras independentes", "Teste de Wilcoxon para postos sinalizados"],
        "corretas": [3],
        "explicacao": "O Wilcoxon para postos sinalizados considera diferenças entre medidas pareadas. Sua interpretação depende das condições do teste, inclusive da distribuição das diferenças."
    },
    {
        "id": 4, "tipo": "unica",
        "texto": "Dois grupos independentes de pacientes recebem tratamentos diferentes. A variável de resposta é o tempo de recuperação em dias, com forte assimetria e valores extremos. O interesse é comparar a tendência de os tempos de um grupo serem maiores que os do outro, sem pressupor normalidade. Qual teste é uma escolha apropriada?",
        "opcoes": ["Teste de Mann–Whitney", "Teste de Wilcoxon para postos sinalizados", "Teste t pareado", "Teste t clássico de amostras independentes"],
        "corretas": [0],
        "explicacao": "Mann–Whitney compara o ordenamento relativo de observações de grupos independentes sem exigir normalidade. Não equivale sempre a testar uma diferença de medianas."
    },
    {
        "id": 5, "tipo": "vf",
        "texto": "No teste t pareado, o pressuposto de normalidade refere-se à distribuição das diferenças entre as duas medidas de cada par, e não necessariamente à distribuição de cada condição separadamente.",
        "opcoes": ["Verdadeiro", "Falso"],
        "corretas": [0],
        "explicacao": "O teste t pareado é calculado com as diferenças intrapares. Para a inferência t clássica em amostras pequenas, considera-se a normalidade aproximada dessas diferenças."
    },
    {
        "id": 6, "tipo": "unica",
        "texto": "Um pesquisador deseja comparar a média do tempo de reação entre dois grupos independentes. Os dados são aproximadamente normais, mas as variâncias populacionais parecem diferentes. Qual procedimento é mais apropriado?",
        "opcoes": ["Utilizar obrigatoriamente o teste de Mann–Whitney", "Aplicar o teste t de Welch para amostras independentes", "Aplicar o teste t pareado com correção das variâncias", "Aplicar o teste de Wilcoxon para postos sinalizados"],
        "corretas": [1],
        "explicacao": "O teste t de Welch compara médias de grupos independentes sem exigir igualdade das variâncias populacionais."
    },
    {
        "id": 7, "tipo": "multipla",
        "texto": "Em relação aos pressupostos e à aplicação dos quatro testes, selecione TODAS as afirmações corretas.",
        "opcoes": [
            "O teste t pareado exige normalidade aproximada das diferenças para a inferência t clássica em amostras pequenas.",
            "O Mann–Whitney pode ser aplicado a duas amostras independentes com observações ordinais.",
            "O Wilcoxon para postos sinalizados exige que as duas amostras sejam independentes.",
            "O teste t para amostras independentes pode utilizar a versão de Welch quando as variâncias diferem."
        ],
        "corretas": [0, 1, 3],
        "explicacao": "São corretas as afirmativas A, B e D. Wilcoxon para postos sinalizados analisa observações pareadas, não amostras independentes."
    },
    {
        "id": 8, "tipo": "unica",
        "texto": "Em um estudo, cada um dos 20 pacientes com uma doença é pareado a um participante saudável de idade e sexo semelhantes. Mede-se uma variável quantitativa contínua uma vez por pessoa, e as diferenças intrapares são aproximadamente normais. O objetivo é comparar a média dessas diferenças. Qual teste é adequado?",
        "opcoes": ["Teste de Mann–Whitney", "Teste t para amostras independentes", "Teste t pareado", "Teste de Wilcoxon para postos sinalizados"],
        "corretas": [2],
        "explicacao": "O teste t pareado também se aplica a pessoas distintas quando elas formam pares estabelecidos no delineamento, e o interesse é a média das diferenças intrapares."
    },
    {
        "id": 9, "tipo": "vf",
        "texto": "Quando dois grupos independentes possuem distribuições com formatos e dispersões muito diferentes, um resultado significativo no teste de Mann–Whitney demonstra necessariamente uma diferença entre as medianas populacionais.",
        "opcoes": ["Verdadeiro", "Falso"],
        "corretas": [1],
        "explicacao": "O Mann–Whitney avalia diferenças na ordenação relativa das observações; com formas/dispersões distintas, um resultado significativo não implica necessariamente diferença entre medianas."
    },
    {
        "id": 10, "tipo": "unica",
        "texto": "Um pesquisador aplica o teste t pareado e encontra p = 0,03 em uma comparação bilateral, adotando α = 0,05. Qual conclusão é estatisticamente justificada?",
        "opcoes": ["A intervenção produziu melhora clinicamente importante em todos os participantes.", "A probabilidade de a hipótese nula ser verdadeira é de 3%.", "A diferença média observada é necessariamente grande.", "Há evidência estatística contra a hipótese de diferença média populacional nula."],
        "corretas": [3],
        "explicacao": "Como p = 0,03 < 0,05, rejeita-se a hipótese nula bilateral. Isso não demonstra automaticamente relevância clínica, causalidade ou efeito grande."
    },
]

LETRAS = "ABCD"
DB_PATH = Path(os.environ.get("QUIZ_DB_PATH", "resultados_quiz.sqlite3"))


def criar_banco():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_utc TEXT NOT NULL,
            nome TEXT NOT NULL,
            matricula TEXT NOT NULL,
            turma TEXT NOT NULL,
            nota INTEGER NOT NULL,
            total INTEGER NOT NULL,
            respostas_json TEXT NOT NULL
        )""")


def guardar_resultado(nome, matricula, turma, respostas, nota):
    criar_banco()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO resultados (data_utc, nome, matricula, turma, nota, total, respostas_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), nome, matricula, turma,
             nota, len(QUESTOES), json.dumps(respostas, ensure_ascii=False)),
        )


def formatar_opcao(q, indice):
    if q["tipo"] == "vf":
        return q["opcoes"][indice]
    return f"{LETRAS[indice]}) {q['opcoes'][indice]}"


def serializar_resposta(q, indices):
    return "; ".join(formatar_opcao(q, i) for i in sorted(indices)) if indices else "Sem resposta"


def resultado_para_csv(nome, matricula, turma, respostas):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Nome", nome])
    writer.writerow(["Matrícula", matricula])
    writer.writerow(["Turma", turma])
    writer.writerow(["Questão", "Resposta do aluno", "Gabarito", "Acertou"])
    for q in QUESTOES:
        atual = respostas[str(q["id"])]
        certo = atual == q["corretas"]
        writer.writerow([q["id"], serializar_resposta(q, atual), serializar_resposta(q, q["corretas"]), "Sim" if certo else "Não"])
    writer.writerow(["Nota", sum(respostas[str(q["id"])] == q["corretas"] for q in QUESTOES)])
    return buf.getvalue().encode("utf-8-sig")


def obter_senha():
    try:
        return st.secrets.get("SENHA_PROFESSOR", os.environ.get("SENHA_PROFESSOR", ""))
    except (FileNotFoundError, KeyError):
        return os.environ.get("SENHA_PROFESSOR", "")


st.title("📊 Qual teste estatístico utilizar?")
st.write("**10 questões • 1 ponto por questão • Bioestatística**")
st.caption("Teste t pareado · Wilcoxon para postos sinalizados · Teste t independente · Mann–Whitney")

aba_aluno, aba_pratica, aba_professor = st.tabs(["🧑‍🎓 Questionário do aluno", "🔬 Atividade prática (CSV)", "👩‍🏫 Área do professor"])

with aba_aluno:
    if not st.session_state.get("concluido", False):
        st.info("Responda todas as questões e clique em **Enviar respostas**. O sistema exibirá a nota e o feedback após o envio.")
        with st.form("form_questionario"):
            nome = st.text_input("Nome completo *", max_chars=150)
            matricula = st.text_input("Matrícula ou identificador *", max_chars=60)
            turma = st.text_input("Turma (opcional)", max_chars=100)
            escolhas = {}
            for q in QUESTOES:
                st.divider()
                st.markdown(f"**Questão {q['id']} — 1 ponto**")
                st.write(q["texto"])
                if q["tipo"] == "multipla":
                    st.caption("Marque todas as alternativas que considerar corretas.")
                    escolhas[str(q["id"])] = [i for i in range(len(q["opcoes"])) if st.checkbox(formatar_opcao(q, i), key=f"q{q['id']}_{i}")]
                else:
                    opc = ["Selecione uma alternativa"] + [formatar_opcao(q, i) for i in range(len(q["opcoes"]))]
                    valor = st.radio("Resposta", opc, index=0, key=f"q{q['id']}", label_visibility="collapsed")
                    escolhas[str(q["id"])] = [] if valor == opc[0] else [opc.index(valor) - 1]
            enviado = st.form_submit_button("Enviar respostas e ver nota", type="primary", use_container_width=True)

        if enviado:
            if not nome.strip() or not matricula.strip():
                st.error("Preencha nome e matrícula/identificador.")
            elif any(not escolhas[str(q["id"])] for q in QUESTOES):
                st.error("Responda todas as 10 questões antes de enviar.")
            else:
                nota = sum(escolhas[str(q["id"])] == q["corretas"] for q in QUESTOES)
                try:
                    guardar_resultado(nome.strip(), matricula.strip(), turma.strip(), escolhas, nota)
                except sqlite3.Error as err:
                    st.warning(f"Não foi possível salvar na base local ({err}). Faça o download do resultado após o envio.")
                st.session_state.update({"concluido": True, "nome_aluno": nome.strip(),
                                         "matricula_aluno": matricula.strip(), "turma_aluno": turma.strip(),
                                         "respostas_aluno": escolhas, "nota_aluno": nota})
                st.rerun()
    else:
        nota = st.session_state["nota_aluno"]
        st.success("Questionário concluído!")
        st.metric("Sua nota", f"{nota} / {len(QUESTOES)}", f"{nota / len(QUESTOES) * 100:.0f}% de acertos", delta_color="off")
        st.write(f"**Aluno(a):** {st.session_state['nome_aluno']}")
        st.subheader("Correção comentada")
        for q in QUESTOES:
            dada = st.session_state["respostas_aluno"][str(q["id"])]
            correto = dada == q["corretas"]
            with st.expander(f"{'✅' if correto else '❌'} Questão {q['id']} — {'Acertou' if correto else 'Errou'}"):
                st.write(q["texto"])
                st.write("**Sua resposta:**", serializar_resposta(q, dada))
                st.write("**Resposta correta:**", serializar_resposta(q, q["corretas"]))
                st.write("**Explicação:**", q["explicacao"])
        st.download_button("📥 Baixar meu resultado (CSV)",
                           resultado_para_csv(st.session_state["nome_aluno"], st.session_state["matricula_aluno"],
                                              st.session_state["turma_aluno"], st.session_state["respostas_aluno"]),
                           file_name="meu_resultado_bioestatistica.csv", mime="text/csv", use_container_width=True)
        if st.button("Iniciar uma nova tentativa neste navegador"):
            for chave in list(st.session_state):
                if chave.startswith("q") or chave in {"concluido", "nome_aluno", "matricula_aluno", "turma_aluno", "respostas_aluno", "nota_aluno"}:
                    del st.session_state[chave]
            st.rerun()

with aba_pratica:
    if st.session_state.get("concluido", False):
        atividade_pratica()
    else:
        st.info("Conclua primeiro as 10 questões do questionário para liberar a atividade prática.")

with aba_professor:
    senha_configurada = obter_senha()
    if not senha_configurada:
        st.warning("A área do professor está desativada. Configure SENHA_PROFESSOR em .streamlit/secrets.toml ou como variável de ambiente.")
    else:
        senha = st.text_input("Senha do professor", type="password", key="senha_digitada")
        if senha and hmac.compare_digest(senha, str(senha_configurada)):
            try:
                criar_banco()
                with sqlite3.connect(DB_PATH) as conn:
                    df = pd.read_sql_query("SELECT data_utc, nome, matricula, turma, nota, total, respostas_json FROM resultados ORDER BY id DESC", conn)
            except sqlite3.Error as err:
                st.error(f"Falha ao abrir o banco de resultados: {err}")
            else:
                st.metric("Tentativas registradas", len(df))
                if not df.empty:
                    st.metric("Nota média (tentativas)", f"{df['nota'].mean():.2f} / {len(QUESTOES)}")
                    st.dataframe(df.drop(columns=["respostas_json"]), hide_index=True, use_container_width=True)
                    st.download_button("📥 Baixar respostas da turma (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                                       "respostas_turma.csv", "text/csv", use_container_width=True)
                    acertos = []
                    for q in QUESTOES:
                        n = sum(json.loads(row)[str(q["id"])] == q["corretas"] for row in df["respostas_json"])
                        acertos.append({"Questão": f"Q{q['id']}", "Percentual de acertos": round(100 * n / len(df), 1)})
                    st.subheader("Percentual de acertos por questão")
                    st.bar_chart(pd.DataFrame(acertos).set_index("Questão"))
                    st.caption("Os percentuais consideram tentativas, não alunos únicos. Tentativas repetidas permanecem registradas.")
                else:
                    st.info("Ainda não existem respostas registradas neste banco de dados.")
        elif senha:
            st.error("Senha incorreta.")

st.divider()
st.caption("Aviso para o professor: os resultados são armazenados em SQLite local. Em hospedagem gratuita do Streamlit Community Cloud, o armazenamento em disco pode ser perdido após reinicializações ou recriações do aplicativo. Para coleta permanente, use um banco de dados externo ou solicite aos alunos os CSVs individuais. Informe aos alunos a finalidade da coleta e limite o acesso aos dados pessoais.")
