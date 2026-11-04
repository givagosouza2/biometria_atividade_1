# Questionário interativo de Bioestatística — Streamlit

Aplicativo com 10 questões sobre **teste t pareado, Wilcoxon para postos sinalizados, teste t para amostras independentes (incluindo Welch) e Mann–Whitney**.

## Funcionalidades
- Nome, matrícula/identificador e turma opcional.
- 10 questões (múltipla escolha, verdadeiro/falso e uma de múltiplas respostas).
- Bloqueia o envio se alguma questão não for respondida.
- Nota de 0 a 10 e correção comentada após envio.
- Download do resultado individual em CSV.
- Área do professor protegida por senha configurável, lista de tentativas e percentual de acerto por questão.
- Registro de tentativas em SQLite local.

## Executar no Windows (PowerShell)

Na pasta do projeto:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Caso `py` não esteja disponível, substitua `py` por `python`.

## Configurar a senha do professor

Crie a pasta `.streamlit` e dentro dela o arquivo `secrets.toml`:

```toml
SENHA_PROFESSOR = "defina-uma-senha-forte"
```

**Não publique esse arquivo no GitHub.** Você também pode adicionar `SENHA_PROFESSOR` diretamente nos Secrets do Streamlit Community Cloud. Sem senha configurada, a área do professor fica desativada.

## Publicar para os alunos

1. Crie um repositório no GitHub com `app.py` e `requirements.txt` (não inclua banco SQLite ou secrets).
2. No Streamlit Community Cloud, selecione esse repositório e escolha `app.py`.
3. Nas configurações do aplicativo, adicione o secret `SENHA_PROFESSOR`.
4. Compartilhe a URL gerada com a turma.

## Importante: persistência e privacidade

Os dados são gravados no arquivo `resultados_quiz.sqlite3` na máquina onde o app roda. Em serviços com armazenamento temporário, como o Streamlit Community Cloud, **as respostas podem ser perdidas** em reinicializações. Para avaliação formal com registro permanente, integre um banco externo persistente com acesso controlado. Até lá, peça que cada aluno baixe e envie seu CSV individual.

O app aceita novas tentativas e registra cada uma como linha distinta; não é uma plataforma antifraude ou de provas com controle de identidade. A área do professor contém dados pessoais; mantenha a senha em segredo e informe aos alunos a finalidade e política de tratamento dos dados.

## Atividade prática após o questionário

A aba **Atividade prática (CSV)** é liberada quando o discente conclui as 10 questões.

- Upload de CSV (até 10 MB), com separador automático, vírgula, ponto e vírgula ou tabulação; escolha do separador decimal.
- CSV didático simulado disponível para download.
- **Uma variável:** estatística descritiva, Shapiro–Wilk, histograma e Q-Q plot.
- **Dois grupos independentes:** análises separadas de cada grupo, histogramas comparativos e homocedasticidade pelo teste de Levene com centro na mediana (Brown–Forsythe).
- **Duas medidas pareadas:** análises dos dois momentos e das diferenças, usando apenas pares completos. O pressuposto de normalidade é verificado **nas diferenças**.
- Estatística descritiva: n válido, ausentes/invalidos, média, mediana, desvio-padrão amostral, variância amostral, erro-padrão, mínimos/máximos, amplitude, quartis, amplitude interquartil, percentis 5 e 95, coeficiente de variação, assimetria e curtose em excesso.
- Roteiro com cinco respostas abertas que permite baixar um relatório em texto e exportar estatísticas descritivas em CSV.

**Interpretação:** p ≥ α em Shapiro–Wilk ou Levene não comprova normalidade ou variâncias iguais. Avalie o delineamento, independência, outliers, gráficos, tamanho amostral e objetivo (médias versus diferenças de distribuição). Wilcoxon para postos sinalizados requer considerar os pressupostos sobre diferenças pareadas; Mann–Whitney não é automaticamente um teste de medianas. O app não recomenda testes de modo automático nem transforma o valor p em regra única.

Os dados carregados **não** são adicionados ao banco SQLite. O discente entrega o relatório gerado separadamente. Não envie informações sensíveis ou identificáveis ao app sem autorização.
