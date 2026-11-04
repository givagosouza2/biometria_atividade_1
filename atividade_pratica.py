"""Atividade de análise exploratória e pressupostos para o quiz de Bioestatística."""
from __future__ import annotations

import io
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

MAX_UPLOAD_MB = 10


def csv_exemplo():
    rng = np.random.default_rng(2026)
    n = 40
    grupo = np.repeat(["Controle", "Intervenção"], n // 2)
    antes = np.round(rng.normal(65, 9, n), 2)
    depois = np.round(antes + np.where(grupo == "Intervenção", 5, 1) + rng.normal(0, 3, n), 2)
    return pd.DataFrame({"id": np.arange(1, n + 1), "grupo": grupo, "antes": antes, "depois": depois})


def ler_csv(arquivo, separador, decimal):
    if arquivo.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"O arquivo ultrapassa o limite de {MAX_UPLOAD_MB} MB.")
    dados = arquivo.getvalue()
    sep = {"Automático": None, "Vírgula (, )": ",", "Ponto e vírgula (; )": ";", "Tabulação": "\t"}[separador]
    return pd.read_csv(io.BytesIO(dados), sep=sep, engine="python" if sep is None else "c", decimal=decimal, encoding="utf-8-sig", on_bad_lines="error")


def colunas_numericas(df):
    candidatas = []
    for col in df.columns:
        serie = pd.to_numeric(df[col], errors="coerce")
        if serie.notna().sum() >= 2:
            candidatas.append(col)
    return candidatas


def descricao(serie):
    s = pd.to_numeric(serie, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    n = len(s)
    base = {"n válido": n, "Ausentes/invalidos": len(serie) - n}
    if not n:
        return {**base, **{x: np.nan for x in ["Média", "Mediana", "Desvio-padrão", "Variância", "Erro-padrão", "Mínimo", "Máximo", "Amplitude", "Q1 (25%)", "Q3 (75%)", "Amplitude interquartil", "P5", "P95", "Coef. variação (%)", "Assimetria (Fisher)", "Curtose excesso (Fisher)"]}}
    media = s.mean()
    dp = s.std(ddof=1) if n > 1 else np.nan
    return {
        **base,
        "Média": media, "Mediana": s.median(), "Desvio-padrão": dp,
        "Variância": s.var(ddof=1) if n > 1 else np.nan,
        "Erro-padrão": dp / np.sqrt(n) if n > 1 else np.nan,
        "Mínimo": s.min(), "Máximo": s.max(), "Amplitude": s.max() - s.min(),
        "Q1 (25%)": s.quantile(.25), "Q3 (75%)": s.quantile(.75),
        "Amplitude interquartil": s.quantile(.75) - s.quantile(.25),
        "P5": s.quantile(.05), "P95": s.quantile(.95),
        "Coef. variação (%)": 100 * dp / abs(media) if n > 1 and not np.isclose(media, 0) else np.nan,
        "Assimetria (Fisher)": s.skew() if n >= 3 else np.nan,
        "Curtose excesso (Fisher)": s.kurt() if n >= 4 else np.nan,
    }


def shapiro_seguro(serie):
    s = pd.to_numeric(serie, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
    if len(s) < 3:
        return None, "Shapiro–Wilk requer pelo menos 3 observações válidas."
    if len(s) > 5000:
        return None, "Shapiro–Wilk não foi calculado: n > 5000 (precisão do valor p pode ser limitada). Inspecione os gráficos."
    if np.ptp(s) == 0:
        return None, "Todos os valores são iguais: Shapiro–Wilk não é informativo."
    try:
        resultado = stats.shapiro(s)
        return {"W": float(resultado.statistic), "p": float(resultado.pvalue), "n": len(s)}, None
    except ValueError as e:
        return None, str(e)


def graficos(serie, titulo):
    s = pd.to_numeric(serie, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
    if not len(s):
        return
    fig1, ax1 = plt.subplots(figsize=(7, 3.8))
    ax1.hist(s, bins="auto" if len(s) > 1 and np.ptp(s) else 1, edgecolor="white")
    ax1.set(xlabel=titulo, ylabel="Frequência", title=f"Histograma — {titulo}")
    fig1.tight_layout()
    st.pyplot(fig1, clear_figure=True)
    plt.close(fig1)
    if len(s) >= 3 and np.std(s) > 0:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        stats.probplot(s, dist="norm", plot=ax2)
        ax2.set(title=f"Q-Q plot normal — {titulo}", xlabel="Quantis teóricos da normal", ylabel="Quantis amostrais")
        fig2.tight_layout()
        st.pyplot(fig2, clear_figure=True)
        plt.close(fig2)
    else:
        st.info("O Q-Q plot exige pelo menos três valores e alguma variabilidade.")


def avaliar_amostra(nome, serie, alpha, apresentar_graficos=True):
    st.markdown(f"#### {nome}")
    resumo = descricao(serie)
    st.dataframe(pd.DataFrame([resumo], index=[nome]).T.rename(columns={nome: "Valor"}).style.format(precision=4, na_rep="—"), use_container_width=True)
    teste, aviso = shapiro_seguro(serie)
    if aviso:
        st.warning(aviso)
    else:
        st.write(f"**Shapiro–Wilk:** W = {teste['W']:.4f}; p = {teste['p']:.4g}; n = {teste['n']}.")
        if teste["p"] < alpha:
            st.write(f"Com α = {alpha:g}, os dados oferecem evidência contra a hipótese de normalidade (p < α).")
        else:
            st.write(f"Com α = {alpha:g}, não há evidência suficiente para rejeitar normalidade (p ≥ α). Isso **não comprova** normalidade.")
    st.caption("Assimetria próxima de zero sugere simetria; curtose em excesso próxima de zero corresponde à referência normal. Não existem limites universais que substituam avaliação gráfica e contextual.")
    if apresentar_graficos:
        graficos(serie, nome)
    return resumo, teste


def comparativo_hist(grupos):
    fig, ax = plt.subplots(figsize=(7, 4))
    for nome, serie in grupos.items():
        s = pd.to_numeric(serie, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if len(s):
            ax.hist(s, bins="auto", alpha=.5, label=str(nome))
    ax.set(xlabel="Valor da variável", ylabel="Frequência", title="Histogramas por grupo")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def relatorio_csv(resumos):
    linhas = []
    for nome, dados in resumos.items():
        linhas.append({"Conjunto": nome, **dados})
    return pd.DataFrame(linhas).to_csv(index=False).encode("utf-8-sig")


def atividade_pratica():
    st.header("Atividade prática — análise exploratória e pressupostos")
    st.write("Carregue um arquivo CSV, configure a estrutura dos dados e interprete os resultados. Esta atividade complementa as 10 questões teóricas.")
    with st.expander("Orientações e modelo de CSV", expanded=False):
        st.write("Use **colunas no cabeçalho**. Para medidas pareadas, cada linha representa um participante e há colunas para os dois momentos. Para grupos independentes, use uma coluna numérica e outra que identifique o grupo.")
        st.dataframe(csv_exemplo().head(6), hide_index=True, use_container_width=True)
        st.download_button("Baixar CSV de exemplo", csv_exemplo().to_csv(index=False).encode("utf-8-sig"), "dados_exemplo_bioestatistica.csv", "text/csv")
        st.caption("Os dados do exemplo são simulados, exclusivamente para ensino.")
    arquivo = st.file_uploader("Selecione um arquivo CSV", type=["csv"], key="atividade_csv")
    if arquivo is None:
        st.info("Para começar, carregue um CSV. Você pode baixar o modelo acima e usá-lo para testar o aplicativo.")
        return
    col1, col2 = st.columns(2)
    with col1:
        separador = st.selectbox("Separador do CSV", ["Automático", "Vírgula (, )", "Ponto e vírgula (; )", "Tabulação"])
    with col2:
        decimal = st.selectbox("Separador decimal", [".", ","], help="O CSV brasileiro costuma usar ponto e vírgula entre colunas e vírgula decimal.")
    try:
        df = ler_csv(arquivo, separador, decimal)
        if df.empty or len(df.columns) < 1:
            st.error("O CSV está vazio ou não contém colunas.")
            return
        if df.columns.duplicated().any():
            st.error("O arquivo possui nomes de colunas duplicados. Renomeie-os antes de continuar.")
            return
    except (pd.errors.ParserError, UnicodeError, ValueError, pd.errors.EmptyDataError) as exc:
        st.error(f"Não foi possível ler o CSV: {exc}")
        return
    st.write(f"**Arquivo:** {df.shape[0]} linhas × {df.shape[1]} colunas")
    with st.expander("Visualização das primeiras linhas"):
        st.dataframe(df.head(15), use_container_width=True, hide_index=True)
    nums = colunas_numericas(df)
    if not nums:
        st.error("Não encontrei variáveis numéricas com pelo menos dois valores válidos. Confira separadores, decimais e cabeçalhos.")
        return
    desenho = st.radio("Como os dados estão organizados?", ["Uma variável", "Dois grupos independentes", "Medidas pareadas (antes/depois)"], horizontal=True)
    alpha = st.selectbox("Nível de significância (α)", [0.05, 0.01, 0.10], index=0)
    resumos = {}
    st.divider()
    if desenho == "Uma variável":
        variavel = st.selectbox("Variável numérica", nums)
        resumos[variavel], _ = avaliar_amostra(variavel, df[variavel], alpha)
        st.info("Se essa variável participar de uma comparação entre dois grupos ou momentos, considere analisar as distribuições pertinentes ao delineamento, e não apenas esta coluna isoladamente.")
    elif desenho == "Dois grupos independentes":
        colunas_grupo = [c for c in df.columns if c not in nums] + [c for c in nums if df[c].nunique(dropna=True) <= 12]
        if not colunas_grupo:
            st.warning("Não encontrei uma coluna categórica para identificar os dois grupos.")
            return
        grupo_col = st.selectbox("Coluna que identifica os grupos", colunas_grupo)
        variaveis = [c for c in nums if c != grupo_col]
        if not variaveis:
            st.warning("É necessário ter uma variável numérica além da coluna de grupos.")
            return
        variavel = st.selectbox("Variável numérica de resposta", variaveis)
        niveis = df[grupo_col].dropna().unique().tolist()
        if len(niveis) < 2:
            st.warning("A coluna de grupos precisa conter ao menos dois valores diferentes.")
            return
        selecionados = st.multiselect("Selecione exatamente dois grupos", niveis, default=niveis[:2], max_selections=2)
        if len(selecionados) != 2:
            st.info("Escolha dois grupos para continuar.")
            return
        grupos = {}
        for nivel in selecionados:
            nome = str(nivel)
            grupos[nome] = df.loc[df[grupo_col] == nivel, variavel]
        for nome, serie in grupos.items():
            resumos[nome], _ = avaliar_amostra(nome, serie, alpha)
        st.subheader("Homogeneidade de variâncias (homocedasticidade)")
        amostras = [pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy() for s in grupos.values()]
        if min(map(len, amostras)) < 2 or any(np.ptp(s) == 0 for s in amostras):
            st.warning("Levene (centro na mediana) não foi calculado: cada grupo deve ter pelo menos dois valores e variabilidade suficiente.")
        else:
            with np.errstate(all="ignore"):
                lev = stats.levene(*amostras, center="median")
            if not np.isfinite(lev.pvalue):
                st.warning("O teste de Levene não produziu um valor p válido.")
            else:
                st.write(f"**Levene/Brown–Forsythe (mediana):** estatística = {lev.statistic:.4f}, p = {lev.pvalue:.4g}.")
                st.write("Há evidência de diferenças entre variâncias." if lev.pvalue < alpha else "Não há evidência suficiente de variâncias diferentes; isso não comprova sua igualdade.")
        st.write("**Comparação visual das distribuições**")
        comparativo_hist(grupos)
        st.caption("Se o objetivo é comparar médias de grupos independentes, o teste t de Welch é geralmente uma escolha robusta quando não se deseja assumir variâncias iguais. A escolha não deve depender mecanicamente de um único valor p de pressuposto.")
    else:
        colunas = st.columns(2)
        with colunas[0]:
            antes = st.selectbox("Coluna do primeiro momento", nums, index=0)
        with colunas[1]:
            opcoes_depois = [x for x in nums if x != antes]
            if not opcoes_depois:
                st.warning("São necessárias duas colunas numéricas para dados pareados.")
                return
            depois = st.selectbox("Coluna do segundo momento", opcoes_depois)
        dados = df[[antes, depois]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        st.write(f"**Pares completos:** {len(dados)} de {len(df)} linhas. Linhas incompletas foram excluídas em pares.")
        if len(dados) < 2:
            st.warning("São necessários pelo menos dois pares completos.")
            return
        diferencas = dados[depois] - dados[antes]
        for nome, serie in [(antes, dados[antes]), (depois, dados[depois]), (f"Diferença ({depois} − {antes})", diferencas)]:
            resumos[nome], _ = avaliar_amostra(nome, serie, alpha)
        st.success("Para o teste t pareado, examine sobretudo a distribuição das **diferenças**. A homocedasticidade entre os dois momentos não é um pressuposto desse teste.")
    st.divider()
    st.download_button("📥 Baixar estatísticas descritivas (CSV)", relatorio_csv(resumos), "estatisticas_descritivas.csv", "text/csv", use_container_width=True)
    st.subheader("Roteiro de interpretação do discente")
    st.write("Registre suas conclusões sobre os dados examinados. As respostas podem ser exportadas e entregues ao professor.")
    with st.form("relatorio_discente"):
        identificacao = st.text_input("Nome ou código do discente", value=st.session_state.get("nome_aluno", ""))
        pergunta1 = st.text_area("1. Descreva tendência central, dispersão, valores extremos e tamanho amostral.")
        pergunta2 = st.text_area("2. O que o histograma e o Q-Q plot indicam? A análise visual concorda com Shapiro–Wilk?")
        pergunta3 = st.text_area("3. Interprete assimetria e curtose. Quais limitações existem nessa interpretação?")
        pergunta4 = st.text_area("4. Se pertinente, interprete homocedasticidade. Caso não se aplique, justifique.")
        pergunta5 = st.text_area("5. Que teste de comparação você escolheria (t pareado, Wilcoxon, t independente/Welch ou Mann–Whitney) e por quê? Considere desenho, variável e objetivo.")
        registrar = st.form_submit_button("Gerar relatório de interpretação", type="primary")
    if registrar:
        respostas = [pergunta1, pergunta2, pergunta3, pergunta4, pergunta5]
        if not identificacao.strip() or any(not resposta.strip() for resposta in respostas):
            st.warning("Preencha a identificação e as cinco respostas para gerar o relatório.")
        else:
            linhas = ["ATIVIDADE PRÁTICA — BIOESTATÍSTICA", f"Discente: {identificacao}", f"Arquivo: {arquivo.name}", f"Desenho: {desenho}", f"Alfa: {alpha}", "", "RESPOSTAS"]
            linhas.extend(f"{i}. {resposta}" for i, resposta in enumerate(respostas, start=1))
            linhas.extend(["", "ESTATÍSTICAS DESCRITIVAS", pd.DataFrame([{"Conjunto": k, **v} for k, v in resumos.items()]).to_csv(index=False)])
            st.download_button("Baixar meu relatório (.txt)", "\n\n".join(linhas).encode("utf-8-sig"), "relatorio_atividade_pratica.txt", "text/plain")
    st.caption("Privacidade: o arquivo enviado é processado apenas durante a sessão da atividade e não é gravado no banco SQLite do questionário. Não carregue dados pessoais sensíveis ou identificáveis sem autorização.")
