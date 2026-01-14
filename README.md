# 📊 POA Budget Analytics (Dashboard Orçamentário)

Este projeto é uma ferramenta de Business Intelligence e Data Storytelling desenvolvida para analisar e visualizar a execução orçamentária do município de Porto Alegre. O objetivo é tornar os dados de finanças públicas (Receitas e Despesas) acessíveis, transparentes e fáceis de entender através de dashboards interativos.

Este trabalho foi desenvolvido como parte do Trabalho de Conclusão de Curso (TCC) de especialização de **Lucas Wodtke**.

## 🚀 Demo Online

Você pode acessar a aplicação rodando em tempo real através do link abaixo:

### [🌐 Acessar Dashboard (Streamlit)](https://poa-orcamento.streamlit.app/)

---

## 📂 Fonte de Dados

Os dados utilizados neste projeto são públicos e foram obtidos através do Portal de Dados Abertos de Porto Alegre. Para executar o projeto localmente com dados atualizados, você precisará baixar as tabelas `.csv` referentes a **Receitas** e **Despesas**.

* **Fonte Oficial:** [Dados Abertos - Porto Alegre](https://dadosabertos.poa.br/)

> **Nota:** O sistema processa dados históricos (2019-2023) e realiza o tratamento de codificação (UTF-8/Latin1) e conversão de formatos monetários brasileiros automaticamente via script ETL.

---

## 🛠️ Funcionalidades

O dashboard conta com três módulos principais de navegação:

### 1. ⚖️ Despesas x Receitas (Balanço Geral)

* **KPIs Financeiros:** Visão rápida do Superávit/Déficit e Autonomia Fiscal.
* **Diagrama de Sankey:** Visualização do fluxo do dinheiro, desde a origem da arrecadação até a função de destino (Saúde, Educação, Obras, etc.).
* **Análise Sazonal:** Comparativo mensal de entradas e saídas de caixa.
* **Glossário Integrado:** Explicações didáticas sobre termos como *Empenho*, *Liquidação*, *ASPS*, *MDE*, etc.

### 2. 💸 Análise Detalhada de Despesas

* **Funil de Execução:** Monitoramento do ciclo de vida da despesa (Orçado → Empenhado → Liquidado → Pago).
* **Decomposição Hierárquica:** Gráficos interativos (Treemap e Sunburst) que permitem explorar a despesa desde a Categoria Econômica até o Elemento de Despesa.
* **Ranking de Gastos:** Top maiores despesas por função ou órgão.

### 3. 💰 Análise Detalhada de Receitas

* **Monitoramento de Arrecadação:** Evolução temporal das receitas (ex: picos de IPTU).
* **Origem dos Recursos:** Detalhamento de receitas correntes (Tributárias, Serviços) e de Capital.

---

## 💻 Como Rodar o Projeto Localmente

### Pré-requisitos

* Python 3.8+
* Git

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/tcc_dashboard_poa.git
cd tcc_dashboard_poa

```

### 2. Instale as dependências

```bash
pip install -r requirements.txt

```

### 3. Configuração dos Dados

Para que o script funcione, crie uma pasta chamada `data` na raiz do projeto e organize os arquivos CSV baixados do portal de dados abertos da seguinte forma:

```text
tcc_dashboard_poa/
├── APP.py
├── ETL.py
├── requirements.txt
└── data/
    ├── receitas/
    │   └── receita.csv
    └── despesas/
        ├── despesas_2019.csv
        ├── despesas_2020.csv
        └── ... (outros arquivos de despesa)

```

### 4. Processamento (ETL)

Antes de rodar o dashboard, execute o script de ETL para unificar os arquivos de despesas e gerar o arquivo necessário para o gráfico de Sankey:

```bash
python ETL.py

```

*Isso criará os arquivos `despesas_unificado.csv` e `dados_sankey_tcc.csv` dentro da pasta `data`.*

### 5. Executar o Dashboard

```bash
streamlit run APP.py

```

---

## 🧪 Tecnologias Utilizadas

* **Linguagem:** Python
* **Framework Web:** [Streamlit](https://streamlit.io/)
* **Manipulação de Dados:** Pandas
* **Visualização:** Plotly Express & Plotly Graph Objects
* **Design:** CSS customizado injetado via Streamlit

---

## 👨‍💻 Autor

**Lucas Wodtke**

*Projeto desenvolvido para fins acadêmicos e de transparência pública.*
