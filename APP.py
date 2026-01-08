import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ==============================================================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="Dashboard Orçamentário POA", page_icon="🔮", layout="wide")

# ==============================================================================
# 2. FUNÇÕES UTILITÁRIAS (FORMATADORES E TRATAMENTO DE DADOS)
# ==============================================================================

def limpar_moeda(valor):
    """
    Converte strings de moeda brasileira (ex: '1.000,00') para float Python.
    Trata valores nulos e vazios.
    """
    if pd.isna(valor) or valor == '':
        return 0.0
    valor_str = str(valor).strip()
    if ',' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return 0.0

def formatar_br(valor):
    """
    Aplica formatação visual de moeda brasileira (R$ X.XXX,XX) para exibição nos gráficos e KPIs.
    """
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==============================================================================
# 3. ESTILIZAÇÃO (CSS PERSONALIZADO)
# ==============================================================================
def aplicar_estilo_futurista():
    """
    Injeta CSS para aplicar o tema 'Dark Neon/Futurista', alterando fontes,
    cores de fundo e componentes nativos do Streamlit.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400&display=swap');
        .stApp { background-color: #050505; color: #E0E0E0; }
        h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00F3FF !important; text-transform: uppercase; }
        section[data-testid="stSidebar"] { background-color: #080808; border-right: 1px solid #00F3FF; }
        div.stRadio > div[role="radiogroup"] { gap: 10px; }
        div.stRadio label { background-color: #0a0a0a; border: 1px solid #00F3FF; padding: 8px 16px; border-radius: 4px; font-family: 'Orbitron', sans-serif; color: #00F3FF !important; cursor: pointer; transition: all 0.3s; text-align: center; }
        div.stRadio label:hover { background-color: rgba(0, 243, 255, 0.2); box-shadow: 0 0 10px #00F3FF; }
        div.stRadio div[role="radio"] { display: none; }
        div[data-testid="stMetric"] { background-color: rgba(0, 20, 40, 0.6); border: 1px solid #00F3FF; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 243, 255, 0.1); }
        div[data-testid="stMetricValue"] { font-family: 'Orbitron', sans-serif; color: #FFFFFF !important; font-size: 26px !important; }
        div[data-testid="stMetricLabel"] { font-family: 'Orbitron', sans-serif; color: #00F3FF !important; font-size: 14px !important; }
        div.stSelectbox > div > div { background-color: #0a0a0a; color: #00F3FF; border: 1px solid #00F3FF; }
        div.stMultiSelect > div > div { background-color: #0a0a0a; color: #E0E0E0; border: 1px solid #00F3FF; }
        span[data-baseweb="tag"] { background-color: rgba(0, 243, 255, 0.2) !important; }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo_futurista()

# ==============================================================================
# 4. COMPONENTES VISUAIS E DE APOIO AO USUÁRIO
# ==============================================================================

def plot_gauge(valor_atual, valor_meta, titulo):
    """
    Gera um gráfico do tipo Bullet/Gauge para medir atingimento de metas.
    """
    fig = go.Figure(go.Indicator(
        mode = "number+gauge+delta",
        value = valor_atual,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': titulo, 'font': {'size': 14, 'color': '#00F3FF', 'family': 'Orbitron'}},
        delta = {'reference': valor_meta, 'relative': True, 'valueformat': '.1%'},
        gauge = {
            'axis': {'range': [None, max(valor_atual, valor_meta)*1.2], 'tickcolor': "white"},
            'bar': {'color': "#00F3FF"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#333",
            'steps': [{'range': [0, valor_meta], 'color': 'rgba(255, 255, 255, 0.1)'}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': valor_meta}
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    return fig

def obter_conceito(termo):
    """
    Dicionário centralizado de conceitos orçamentários para tooltips e explicações.
    """
    conceitos = {
        "orçamento": "**Orçamento Público:** Instrumento pelo qual o governo estima as receitas e fixa as despesas para controlar as finanças e executar ações.",
        "empenho": "**Despesa Empenhada (Reserva):** Valor do orçamento formalmente reservado para compromissos assumidos com terceiros. É o primeiro estágio da execução.",
        "liquidacao": "**Despesa Liquidada (Entrega):** Verificação do direito do credor. Significa que o bem foi entregue ou o serviço prestado. Antecede o pagamento.",
        "superavit": "**Superávit Orçamentário:** Diferença positiva entre a receita arrecadada e a despesa empenhada. Indica que sobrou recurso no período.",
        "correntes_desp": "**Despesa Corrente (Manutenção):** Destina-se à manutenção da máquina pública (salários, luz, material de consumo) e funcionamento dos serviços.",
        "capital_desp": "**Despesa de Capital (Investimento):** Focada no incremento da capacidade produtiva, como obras, aquisição de equipamentos ou amortização de dívidas.",
        "receita_corrente": "**Receita Corrente:** Recursos captados para cobrir despesas de manutenção. Inclui impostos (IPTU, ISS), taxas e transferências.",
        "receita_capital": "**Receita de Capital:** Proveniente de operações de crédito (empréstimos), alienação de bens (venda de imóveis) ou amortizações.",
        "asps": "**ASPS (Saúde):** Ações e Serviços Públicos de Saúde - gastos mínimos constitucionais obrigatórios.",
        "mde": "**MDE (Educação):** Manutenção e Desenvolvimento do Ensino - recursos vinculados à educação básica.",
        "fundeb": "**FUNDEB:** Fundo de Manutenção e Desenvolvimento da Educação Básica e Valorização dos Profissionais.",
        "iptu": "**IPTU:** Imposto Predial e Territorial Urbano.",
        "iss": "**ISS:** Imposto Sobre Serviços de Qualquer Natureza."
    }
    return conceitos.get(termo, "")

def box_educativo(titulo, termos_chaves):
    """
    Gera um componente expansível contendo definições teóricas.
    """
    with st.expander(f"📚 Entenda: {titulo}", expanded=False):
        for t in termos_chaves:
            st.markdown(f"• {obter_conceito(t)}")

def guia_visual(texto_markdown):
    """
    Cria um botão de ajuda (Popover) com instruções de interpretação dos gráficos.
    """
    with st.popover("🧠 Como interpretar esse gráfico?"):
        st.markdown("### 🤓 Guia de Leitura")
        st.markdown(texto_markdown)

# ==============================================================================
# 5. CARREGAMENTO E TRATAMENTO DE DADOS (ETL)
# ==============================================================================

@st.cache_data
def carregar_dados():
    base_path = r'data' 
    caminho_rec = os.path.join(base_path, 'receitas', 'receita.csv')
    
    # Conversores para garantir que colunas numéricas sejam lidas corretamente
    conversores_rec = {'valor_arrecadado': limpar_moeda, 'valor_orcado': limpar_moeda}
    
    # Tratamento de encoding (UTF-8 padrão, com fallback para Latin1 se necessário)
    try:
        df_rec = pd.read_csv(caminho_rec, sep=';', encoding='utf-8', converters=conversores_rec)
    except:
        df_rec = pd.read_csv(caminho_rec, sep=';', encoding='latin1', converters=conversores_rec)
        
    df_rec.rename(columns={'ano': 'ano_exercicio', 'valor_arrecadado': 'valor_realizado'}, inplace=True)
    
    # Carregamento de Despesas (Arquivo Unificado)
    caminho_desp = os.path.join(base_path, 'despesas', 'despesas_unificado.csv')
    df_desp = pd.read_csv(caminho_desp, sep=';', encoding='utf-8', decimal=',')
    
    # Padronização de nomes de colunas
    df_desp.rename(columns={
        'exercicio': 'ano_exercicio', 
        'vlpag': 'valor_realizado', 
        'vlorcini': 'valor_orcado', 
        'vlemp': 'valor_empenhado', 
        'vlliq': 'valor_liquidado'
    }, inplace=True)
    
    # Padronização de strings (Upper case e strip)
    if 'desc_funcao' in df_desp.columns: df_desp['desc_funcao'] = df_desp['desc_funcao'].astype(str).str.strip().str.upper()
    if 'nome_orgao' in df_desp.columns: df_desp['nome_orgao'] = df_desp['nome_orgao'].astype(str).str.strip().str.upper()
        
    return df_rec, df_desp

df_receita, df_despesa = carregar_dados()
df_sankey_ready = pd.read_csv(os.path.join(r'data', 'dados_sankey_tcc.csv'), sep=';', decimal=',')

# ==============================================================================
# 6. SIDEBAR: FILTROS GLOBAIS
# ==============================================================================
st.sidebar.title("Configurações")
st.sidebar.markdown("### 📅 Exercício Fiscal")

anos_permitidos = [2019, 2020, 2021, 2022, 2023]
anos_nos_dados = sorted(df_receita['ano_exercicio'].unique())
anos_disp = [a for a in anos_nos_dados if a in anos_permitidos]
if not anos_disp: anos_disp = anos_permitidos
opcoes_ano = anos_disp + ["COMPARADOR DE ANOS"]

selecao_sidebar = st.sidebar.selectbox("Selecione o Modo Temporal:", options=opcoes_ano, index=len(anos_disp)-1)

# Lógica de seleção (Ano Único vs Múltiplos Anos)
if selecao_sidebar == "COMPARADOR DE ANOS":
    anos_selecionados = st.sidebar.multiselect("Escolha os anos:", options=anos_disp, default=anos_disp[-2:])
    if not anos_selecionados: anos_selecionados = [anos_disp[-1]]
    lista_anos_filtro = anos_selecionados
    label_ano_titulo = f"Comparativo ({', '.join(map(str, sorted(lista_anos_filtro)))})"
else:
    lista_anos_filtro = [selecao_sidebar]
    label_ano_titulo = str(selecao_sidebar)

st.sidebar.markdown("---")
st.sidebar.info(f"Visualizando: **{label_ano_titulo}**")

# ==============================================================================
# 7. CABEÇALHO PRINCIPAL E MENU DE NAVEGAÇÃO
# ==============================================================================
st.title("POA Budget Analytics")
visao_selecionada = st.radio("Navegação Principal", options=["DESPESAS X RECEITAS", "APENAS DESPESAS", "APENAS RECEITAS"], index=0, horizontal=True, label_visibility="collapsed")
st.sidebar.markdown("---")

with st.sidebar.expander("🔍 Siglas Comuns"):
    st.caption(obter_conceito('asps'))
    st.caption(obter_conceito('mde'))
    st.caption(obter_conceito('fundeb'))
    st.caption("**LRF:** Lei de Responsabilidade Fiscal.")

st.markdown("---")

# Aplicação dos filtros temporais nos dataframes
rec_ano = df_receita[df_receita['ano_exercicio'].isin(lista_anos_filtro)]
desp_ano = df_despesa[df_despesa['ano_exercicio'].isin(lista_anos_filtro)]

# ==============================================================================
# 8. MÓDULO: DESPESAS X RECEITAS (BALANÇO GERAL)
# ==============================================================================
if visao_selecionada == "DESPESAS X RECEITAS":
    
    st.header(f"⚖️ Balanço Geral - {label_ano_titulo}")
    st.caption("Monitor de Saúde Financeira: Entradas vs Saídas")
    box_educativo("O Equilíbrio das Contas", ["orcamento", "superavit"])
    
    # Cálculo de KPIs Globais
    total_rec = rec_ano['valor_realizado'].sum()
    total_desp = desp_ano['valor_realizado'].sum()
    resultado = total_rec - total_desp
    status_cor = "#00FF99" if resultado >= 0 else "#FF0055"
    
    # Estimativa de Receita Própria vs Total
    if 'nome_origem' in rec_ano.columns:
        rec_propria = rec_ano[rec_ano['nome_origem'].str.contains('TRIBUTÁRIA|PATRIMONIAL|SERVIÇOS', case=False, na=False)]['valor_realizado'].sum()
    else:
        rec_propria = 0
    autonomia_pct = (rec_propria / total_rec * 100) if total_rec > 0 else 0

    # Exibição dos Cards (KPIs)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 RECEITA TOTAL", formatar_br(total_rec), delta="Entradas de Caixa")
    kpi2.metric("💸 DESPESA TOTAL", formatar_br(total_desp), delta="-Saídas de Caixa", delta_color="inverse")
    kpi3.metric("⚖️ RESULTADO", formatar_br(resultado), delta=f"{(resultado/total_rec*100):.1f}% de Margem" if total_rec else None, delta_color="normal" if resultado >=0 else "inverse")
    kpi4.metric("🏛️ AUTONOMIA FISCAL", f"{autonomia_pct:.1f}%", help="% de Receitas Próprias (Tributária, Patrimonial, Serviços) sobre o Total.")

    st.markdown("---")

    # Sub-navegação do Módulo
    modo_balanco = st.radio(
        "Modo de Análise:", 
        ["VISÃO MACRO (Fluxo Geral)", "VISÃO DETALHADA (Por Área)", "COMPARADOR AVANÇADO (Correlações)"], 
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # --- ABA 1: VISÃO MACRO (FLUXO) ---
    if modo_balanco == "VISÃO MACRO (Fluxo Geral)":
        
        # Gráfico Comparativo de Barras
        st.subheader("1. Equilíbrio das Contas")
        col_bal1, col_bal2 = st.columns([3, 1])
        
        with col_bal1:
            df_balanco = pd.DataFrame({
                'Tipo': ['Receitas', 'Despesas'],
                'Valor': [total_rec, total_desp],
                'Cor': ['#00FF99', '#FF0055']
            })
            
            fig_bal = px.bar(df_balanco, x='Valor', y='Tipo', orientation='h', text_auto='.2s', color='Tipo',
                             color_discrete_map={'Receitas': '#00FF99', 'Despesas': '#FF0055'})
            fig_bal.update_layout(height=200, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                                  title="Termômetro Financeiro (Total do Período)", font=dict(family="Orbitron"))
            fig_bal.update_traces(textfont_size=16, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig_bal, use_container_width=True)
            
        with col_bal2:
            st.info("💡 **Análise Rápida:**")
            if resultado > 0:
                st.markdown(f"As contas fecharam no **AZUL**.<br>Superávit de **{formatar_br(resultado)}** disponível para investimentos ou reserva.", unsafe_allow_html=True)
            else:
                st.markdown(f"As contas fecharam no **VERMELHO**.<br>Déficit de **{formatar_br(resultado)}**. Necessário rever gastos ou buscar financiamento.", unsafe_allow_html=True)

        st.markdown("---")

        # Diagrama de Sankey (Receitas -> Cofre -> Despesas)
        st.subheader("2. O Fluxo do Dinheiro (Origem ➝ Cofre ➝ Destino)")
        
        guia_visual("""
        Este gráfico é um **Diagrama de Sankey**. Ele mostra o caminho do dinheiro:
        1.  **Esquerda (Origem):** De onde vem o dinheiro (Impostos, Repasses).
        2.  **Centro (Cofre):** O Tesouro Municipal.
        3.  **Direita (Destino):** Onde o dinheiro foi gasto (Saúde, Educação, Obras).
        
        **Dica:** A **largura** das linhas é proporcional ao valor. Linhas grossas indicam as maiores fontes de receita ou as maiores áreas de gasto.
        """)
        st.caption("Rastreie como a arrecadação se transforma em serviços públicos.")

        c_sk1, c_sk2 = st.columns(2)
        with c_sk1:
            top_n_rec = st.slider("🔍 Zoom Receitas (Top Fontes):", 3, 20, 8)
        with c_sk2:
            top_n_desp = st.slider("🔍 Zoom Despesas (Top Funções):", 3, 20, 8)

        # Preparação dos dados para o Sankey
        # Lado Esquerdo: Receitas
        grp_rec = rec_ano.groupby('nome_origem')['valor_realizado'].sum().reset_index()
        grp_rec.sort_values('valor_realizado', ascending=False, inplace=True)
        top_origens = grp_rec.head(top_n_rec)['nome_origem'].tolist()
        rec_ano['origem_sankey'] = rec_ano['nome_origem'].apply(lambda x: x if x in top_origens else 'OUTRAS FONTES')
        
        df_flow_in = rec_ano.groupby('origem_sankey')['valor_realizado'].sum().reset_index()
        df_flow_in['source'] = df_flow_in['origem_sankey']
        df_flow_in['target'] = "TESOURO MUNICIPAL"
        df_flow_in['color_link'] = "rgba(0, 255, 153, 0.3)"

        # Lado Direito: Despesas
        grp_desp = desp_ano.groupby('desc_funcao')['valor_realizado'].sum().reset_index()
        grp_desp.sort_values('valor_realizado', ascending=False, inplace=True)
        top_funcoes = grp_desp.head(top_n_desp)['desc_funcao'].tolist()
        desp_ano['funcao_sankey'] = desp_ano['desc_funcao'].apply(lambda x: x if x in top_funcoes else 'OUTRAS FUNÇÕES')
        
        df_flow_out = desp_ano.groupby('funcao_sankey')['valor_realizado'].sum().reset_index()
        df_flow_out['source'] = "TESOURO MUNICIPAL"
        df_flow_out['target'] = df_flow_out['funcao_sankey']
        df_flow_out['color_link'] = "rgba(255, 0, 85, 0.3)"

        # União dos fluxos e construção do gráfico
        all_flows = pd.concat([df_flow_in[['source', 'target', 'valor_realizado', 'color_link']], 
                               df_flow_out[['source', 'target', 'valor_realizado', 'color_link']]])
        
        all_nodes = list(pd.concat([all_flows['source'], all_flows['target']]).unique())
        node_map = {name: i for i, name in enumerate(all_nodes)}
        
        node_colors = []
        for n in all_nodes:
            if n == "TESOURO MUNICIPAL": node_colors.append("#FFFFFF")
            elif n in df_flow_in['source'].values: node_colors.append("#00FF99")
            else: node_colors.append("#FF0055")

        fig_sankey_int = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15, thickness=20, line=dict(color="black", width=0.5),
                label=all_nodes, color=node_colors,
                hovertemplate='%{label}<br>Total: R$ %{value:,.2f}<extra></extra>'
            ),
            link=dict(
                source=all_flows['source'].map(node_map),
                target=all_flows['target'].map(node_map),
                value=all_flows['valor_realizado'],
                color=all_flows['color_link']
            )
        )])
        
        fig_sankey_int.update_layout(
            title="Fluxo Integrado de Recursos",
            height=600, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Orbitron", size=12)
        )
        st.plotly_chart(fig_sankey_int, use_container_width=True)

        st.markdown("---")

        # Linha do Tempo (Sazonalidade)
        st.subheader("3. Histórico Mensal (Sazonalidade)")
        
        guia_visual("""
        Este gráfico compara a entrada (**Verde**) e a saída (**Vermelho**) de dinheiro mês a mês.
        * **Área Sombreada:** Mostra visualmente o saldo acumulado.
        * **Picos Verdes:** Geralmente ocorrem no início do ano (pagamento de IPTU à vista) ou recebimento de repasses extras.
        * **Atenção:** Se a linha vermelha cruzar a verde e ficar por cima, significa que naquele mês o município gastou mais do que arrecadou (Déficit Mensal).
        """)
        
        r_mes = rec_ano.groupby(['mes'])['valor_realizado'].sum().reset_index()
        d_mes = desp_ano.groupby(['mes'])['valor_realizado'].sum().reset_index()
        
        df_time = pd.merge(r_mes, d_mes, on='mes', suffixes=('_rec', '_desp'))
        try:
            df_time['mes_num'] = pd.to_numeric(df_time['mes'])
            df_time.sort_values('mes_num', inplace=True)
        except:
            pass
            
        fig_line_mix = go.Figure()
        fig_line_mix.add_trace(go.Scatter(x=df_time['mes'], y=df_time['valor_realizado_rec'], mode='lines+markers', name='Receitas', line=dict(color='#00FF99', width=3)))
        fig_line_mix.add_trace(go.Scatter(x=df_time['mes'], y=df_time['valor_realizado_desp'], mode='lines+markers', name='Despesas', line=dict(color='#FF0055', width=3)))
        fig_line_mix.add_trace(go.Scatter(x=df_time['mes'], y=df_time['valor_realizado_rec'], fill='tonexty', fillcolor='rgba(0,0,0,0)', showlegend=False))

        fig_line_mix.update_layout(height=400, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", title="Dinâmica de Caixa ao Longo do Ano", hovermode="x unified")
        st.plotly_chart(fig_line_mix, use_container_width=True)

        # Sunburst Lado a Lado (Comparação de Estrutura)
        st.subheader("4. Quem Paga vs Quem Gasta")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### 📥 Origem (Receitas)")
            if 'nome_especie' in rec_ano.columns:
                df_sun_r = rec_ano.copy()
                cols_rec_fix = ['nome_origem', 'nome_especie']
                for c in cols_rec_fix:
                    df_sun_r[c] = df_sun_r[c].fillna("NÃO CLASSIFICADO").replace('', 'NÃO CLASSIFICADO')
                
                df_sun_r_agg = df_sun_r.groupby(['nome_origem', 'nome_especie'])['valor_realizado'].sum().reset_index()
                df_sun_r_agg = df_sun_r_agg[df_sun_r_agg['valor_realizado'] > 0]
                
                fig_sun_rec = px.sunburst(df_sun_r_agg, path=['nome_origem', 'nome_especie'], values='valor_realizado', color_discrete_sequence=px.colors.sequential.Emrld)
                fig_sun_rec.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_sun_rec, use_container_width=True)
        
        with col_c2:
            st.markdown("#### 📤 Destino (Despesas)")
            if 'desc_funcao' in desp_ano.columns:
                df_sun_d = desp_ano.copy()
                cols_desp_fix = ['desc_funcao', 'desc_categoria']
                for c in cols_desp_fix:
                    df_sun_d[c] = df_sun_d[c].fillna("NÃO CLASSIFICADO").replace('', 'NÃO CLASSIFICADO')
                
                df_sun_d_agg = df_sun_d.groupby(['desc_funcao', 'desc_categoria'])['valor_realizado'].sum().reset_index()
                df_sun_d_agg = df_sun_d_agg[df_sun_d_agg['valor_realizado'] > 0]

                fig_sun_desp = px.sunburst(df_sun_d_agg, path=['desc_funcao', 'desc_categoria'], values='valor_realizado', color_discrete_sequence=px.colors.sequential.RdBu)
                fig_sun_desp.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_sun_desp, use_container_width=True)

    # --- ABA 2: VISÃO DETALHADA (DRILL-DOWN) ---
    elif modo_balanco == "VISÃO DETALHADA (Por Área)":
        st.markdown("### 🔭 Zoom: Análise Específica por Área")
        
        lista_funcoes = sorted(desp_ano['desc_funcao'].unique())
        funcao_sel = st.selectbox("Selecione a Função de Governo (Área de Gasto):", lista_funcoes)
        
        # Contextualização da área selecionada
        df_d_foco = desp_ano[desp_ano['desc_funcao'] == funcao_sel]
        v_gasto_area = df_d_foco['valor_realizado'].sum()
        pct_orcamento = (v_gasto_area / total_desp * 100) if total_desp > 0 else 0
        
        col_det1, col_det2, col_det3 = st.columns([1, 1, 2])
        with col_det1:
            st.metric(f"Gasto em {funcao_sel}", formatar_br(v_gasto_area))
        with col_det2:
            st.metric("Representatividade", f"{pct_orcamento:.1f}% das Despesas")
            st.progress(pct_orcamento/100)
        with col_det3:
            st.info(f"Visualizando dados exclusivos de **{funcao_sel}** comparados ao total do município.")

        st.markdown("---")
        
        c_funil, c_timeline = st.columns([1, 2])
        
        with c_funil:
            st.subheader("Funil de Execução")
            vals = [
                df_d_foco['valor_orcado'].sum(), 
                df_d_foco['valor_empenhado'].sum(), 
                df_d_foco['valor_liquidado'].sum(), 
                df_d_foco['valor_realizado'].sum()
            ]
            fig_fun = go.Figure(go.Funnel(
                y=["Orçado", "Empenhado", "Liquidado", "Pago"], x=vals,
                texttemplate="%{value:,.2s}", marker={"color": ["#002233", "#005577", "#0099AA", "#00F3FF"]}
            ))
            fig_fun.update_layout(height=300, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20))
            st.plotly_chart(fig_fun, use_container_width=True)
            
        with c_timeline:
            st.subheader("Timeline: Desembolso Específico")
            if 'mes' in df_d_foco.columns:
                time_foco = df_d_foco.groupby('mes')['valor_realizado'].sum().reset_index()
                fig_tf = px.bar(time_foco, x='mes', y='valor_realizado', title=f"Pagamentos Mensais - {funcao_sel}")
                fig_tf.update_traces(marker_color='#00F3FF')
                fig_tf.update_layout(height=300, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_tf, use_container_width=True)

        st.subheader("Onde o dinheiro desta área foi parar?")
        if 'desc_elemento' in df_d_foco.columns:
            top_elem = df_d_foco.groupby('desc_elemento')['valor_realizado'].sum().nlargest(10).reset_index()
            fig_bar_elem = px.bar(top_elem, x='valor_realizado', y='desc_elemento', orientation='h', title="Top 10 Itens de Despesa")
            fig_bar_elem.update_layout(yaxis=dict(autorange="reversed"), template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar_elem, use_container_width=True)

    # --- ABA 3: COMPARADOR AVANÇADO ---
    elif modo_balanco == "COMPARADOR AVANÇADO (Correlações)":
        st.markdown("### 🔬 Laboratório de Correlação")
        st.caption("Analise se o aumento da arrecadação impacta diretamente as despesas.")

        col_sel_comp1, col_sel_comp2 = st.columns(2)
        with col_sel_comp1:
            eixo_x = st.selectbox("Eixo X (Causa?):", ["Receita Total", "Receita Tributária (Própria)", "Transferências"])
        with col_sel_comp2:
            eixo_y = st.multiselect("Eixo Y (Efeito?):", lista_funcoes if 'lista_funcoes' in locals() else sorted(desp_ano['desc_funcao'].unique()), default=["SAÚDE", "EDUCAÇÃO"] if "SAÚDE" in sorted(desp_ano['desc_funcao'].unique()) else None)

        if not eixo_y:
            st.warning("Selecione pelo menos uma função de despesa.")
            st.stop()

        # Preparação dos dados para correlação (Scatterplot)
        rec_mes = rec_ano.groupby(['mes'])['valor_realizado'].sum().reset_index()
        
        if eixo_x == "Receita Tributária (Própria)":
             rec_mes = rec_ano[rec_ano['nome_origem'].str.contains('TRIBUTÁRIA', na=False)].groupby(['mes'])['valor_realizado'].sum().reset_index()
        elif eixo_x == "Transferências":
             rec_mes = rec_ano[rec_ano['nome_origem'].str.contains('TRANSFER', na=False)].groupby(['mes'])['valor_realizado'].sum().reset_index()
        
        rec_mes.rename(columns={'valor_realizado': 'Valor_X'}, inplace=True)
        desp_comp = desp_ano[desp_ano['desc_funcao'].isin(eixo_y)].groupby(['mes', 'desc_funcao'])['valor_realizado'].sum().reset_index()
        df_corr = pd.merge(desp_comp, rec_mes, on='mes')
        
        col_graph1, col_graph2 = st.columns([2, 1])
        
        with col_graph1:
            fig_scat_adv = px.scatter(
                df_corr, x='Valor_X', y='valor_realizado', color='desc_funcao',
                size='valor_realizado', hover_data=['mes'],
                title=f"Correlação: {eixo_x} vs Gastos Selecionados",
                labels={'Valor_X': f"Valor {eixo_x}", 'valor_realizado': 'Despesa Realizada'}
            )
            fig_scat_adv.update_layout(height=400, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_scat_adv, use_container_width=True)
            
        with col_graph2:
            st.subheader("Matriz de Intensidade")
            fig_hm = px.density_heatmap(df_corr, x='desc_funcao', y='Valor_X', z='valor_realizado', nbinsy=10, title="Concentração de Gastos")
            fig_hm.update_layout(height=400, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hm, use_container_width=True)

# ==============================================================================
# 9. MÓDULO: APENAS DESPESAS
# ==============================================================================
elif visao_selecionada == "APENAS DESPESAS":
    st.header(f"Análise de Despesas - {label_ano_titulo}")
    
    # Seletor de Agrupamento
    criterio = st.radio("Critério de Análise:", options=["POR FUNÇÃO", "POR ÓRGÃO"], horizontal=True)
    col_analise = 'desc_funcao' if criterio == "POR FUNÇÃO" else 'nome_orgao'
    lbl_analise = "Função" if criterio == "POR FUNÇÃO" else "Órgão"
    
    st.markdown("---")
    
    # Bloco de KPIs do Ciclo de Vida da Despesa
    st.subheader("Ciclo de Vida da Despesa")
    with st.expander("ℹ️ O que significam esses estágios?", expanded=False):
        st.markdown(f"""
        O dinheiro público percorre três etapas obrigatórias:
        1. {obter_conceito('empenho')}
        2. {obter_conceito('liquidacao')}
        3. **Pagamento:** O dinheiro sai efetivamente da conta da Prefeitura.
        """)
      
    cols_necessarias = ['valor_orcado', 'valor_empenhado', 'valor_liquidado', 'valor_realizado']
    if all(col in desp_ano.columns for col in cols_necessarias):
        
        guia_visual(f"""
        O **Funil de Execução** mostra a "perda de carga" do orçamento:
        1.  **Orçado (Topo):** A intenção de gasto aprovada na Lei Orçamentária.
        2.  **Empenhado:** O valor reservado para contratos.
        3.  **Liquidado:** O serviço foi entregue.
        4.  **Pago (Fundo):** O dinheiro saiu da conta.
        """)
        
        k1, k2, k3, k4 = st.columns(4)
        v_orc = desp_ano['valor_orcado'].sum()
        v_emp = desp_ano['valor_empenhado'].sum()
        v_liq = desp_ano['valor_liquidado'].sum()
        v_pag = desp_ano['valor_realizado'].sum()
       
        # Debug para conferência no terminal do servidor (não afeta o usuário)
        print(f"\n--- CONFERÊNCIA DE VALORES ({label_ano_titulo}) ---")
        print(f"Total Orçado (v_orc):    R$ {v_orc:,.2f}")
        print(f"Total Empenhado (v_emp): R$ {v_emp:,.2f}")
        print(f"Total Liquidado (v_liq): R$ {v_liq:,.2f}")
        print(f"Total Pago (v_pag):      R$ {v_pag:,.2f}")
        print("-" * 50 + "\n")

        k1.metric("1. ORÇADO (Planejado)", f"R$ {v_orc:,.2f}")
        k2.metric("2. EMPENHADO (Reservado)", f"R$ {v_emp:,.2f}", delta=f"{(v_emp/v_orc*100):.1f}% do Orçamento" if v_orc else "0%")
        k3.metric("3. LIQUIDADO (Executado)", f"R$ {v_liq:,.2f}", delta=f"{(v_liq/v_emp*100):.1f}% do Empenho" if v_emp else "0%")
        k4.metric("4. PAGO (Efetivado)", f"R$ {v_pag:,.2f}", delta=f"{(v_pag/v_liq*100):.1f}% do Liquidado" if v_liq else "0%")
        
        # Função auxiliar para formatar rótulos do Funil
        def fmt_curto(v):
            if v >= 1e9: return f"R$ {v/1e9:.2f}B"
            elif v >= 1e6: return f"R$ {v/1e6:.1f}M"
            return f"R$ {v:,.0f}"

        valores = [v_orc, v_emp, v_liq, v_pag]
        textos_curtos = [fmt_curto(v) for v in valores]

        fig_funnel = go.Figure(go.Funnel(
            y = ["Orçado", "Empenhado", "Liquidado", "Pago"],
            x = valores,
            text = textos_curtos,
            textinfo = "text+percent initial",
            textposition = "auto",
            marker = {"color": ["#002233", "#005577", "#0099AA", "#00F3FF"], "line": {"width": 1, "color": "#00F3FF"}},
            connector = {"line": {"color": "#555", "dash": "dot", "width": 1}}
        ))

        fig_funnel.update_layout(
            title={'text': "Funil de Execução Orçamentária", 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
            height=500,
            margin=dict(l=100, r=20, t=50, b=50),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Orbitron", size=14)
        )
        st.plotly_chart(fig_funnel, use_container_width=True)
    else:
        st.error("Erro: Colunas de execução orçamentária não encontradas no arquivo.")
        
    st.markdown("---") 

    # Ranking das Maiores Despesas
    st.subheader("🏆 Ranking das Maiores Despesas")
    
    c_rank1, c_rank2 = st.columns([1, 2])
    with c_rank1:
        qtd_top_bar = st.slider("Quantidade de itens no Top:", min_value=5, max_value=30, value=10, step=5)
    with c_rank2:
        opcao_ranking = st.radio(
            "Agrupamento do Ranking:", 
            [f"Por {lbl_analise} (Visão Macro)", "Por Elemento de Despesa (Detalhado)"], 
            horizontal=True
        )

    col_ranking = col_analise if "Visão Macro" in opcao_ranking else 'desc_elemento'
    
    if col_ranking in desp_ano.columns:
        df_ranking = desp_ano.groupby(col_ranking)['valor_realizado'].sum().reset_index()
        df_ranking = df_ranking.sort_values(by='valor_realizado', ascending=False).head(qtd_top_bar)
        
        df_ranking['label_txt'] = df_ranking['valor_realizado'].apply(
            lambda x: f"R$ {x/1e9:.2f}B" if x >= 1e9 else (f"R$ {x/1e6:.1f}M" if x >= 1e6 else f"R$ {x:,.0f}")
        )

        fig_bar_top = px.bar(
            df_ranking, x='valor_realizado', y=col_ranking, orientation='h', text='label_txt', title=None
        )

        fig_bar_top.update_traces(
            marker_color='#00F3FF', marker_line_color='#FFFFFF', marker_line_width=1,
            textposition='outside', cliponaxis=False
        )

        fig_bar_top.update_layout(
            yaxis=dict(autorange="reversed", title=None, tickfont=dict(size=13)), 
            xaxis=dict(showgrid=True, gridcolor='#333', title="Valor Pago (R$)"),
            height=max(400, qtd_top_bar * 40), 
            margin=dict(l=0, r=50, t=30, b=30),
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Orbitron", size=12)
        )

        st.plotly_chart(fig_bar_top, use_container_width=True)
    else:
        st.warning(f"Coluna '{col_ranking}' não encontrada para gerar o ranking.")

    st.markdown("---")

    # Cadeia de Composição da Despesa (Sankey Hierárquico)
    st.subheader("🔗 Cadeia de Composição da Despesa")
    
    guia_visual("""
    Este fluxo desmembra a despesa em níveis de detalhe técnico:
    1.  **Categoria (Esquerda):** Divide entre manter a máquina (**Corrente**) ou investir (**Capital**).
    2.  **Natureza (Meio):** O tipo de gasto (ex: Pessoal, Juros, Material).
    3.  **Elemento (Direita):** O objeto final da compra (ex: Combustíveis, Medicamentos).
    """)
    st.caption("Fluxo detalhado: Categoria Econômica ➝ Grupo de Natureza ➝ Elemento")

    cols_fluxo = ['desc_categoria', 'desc_natureza', 'desc_elemento']
    
    if all(c in desp_ano.columns for c in cols_fluxo):
        
        c_sankey1, c_sankey2 = st.columns([2, 1])
        with c_sankey1:
            qtd_elementos = st.slider("Quantidade de Elementos (Detalhe Final):", min_value=5, max_value=100, value=20, step=5)
        
        # Filtro de dados para não poluir o gráfico
        df_sankey_gen = desp_ano.copy()
        df_sankey_gen[cols_fluxo] = df_sankey_gen[cols_fluxo].fillna("NÃO INFORMADO")
        
        top_elementos = df_sankey_gen.groupby('desc_elemento')['valor_realizado'].sum().nlargest(qtd_elementos).index.tolist()
        df_filtered = df_sankey_gen[df_sankey_gen['desc_elemento'].isin(top_elementos)]
        df_agg = df_filtered.groupby(cols_fluxo)['valor_realizado'].sum().reset_index()

        altura_dinamica = max(600, len(top_elementos) * 35)

        # Construção dos nós e links
        nodes = []
        links = []
        node_map = {}
        
        def add_node(key, label, color="rgba(0, 243, 255, 0.5)"):
            if key not in node_map:
                node_map[key] = len(nodes)
                nodes.append({"label": label, "color": color})
            return node_map[key]

        add_node("ROOT", "DESPESAS TOTAIS", "#FFFFFF")

        for idx, row in df_agg.iterrows():
            v = row['valor_realizado']
            c_lbl = row['desc_categoria']
            n_lbl = row['desc_natureza']
            e_lbl = row['desc_elemento']

            key_c = f"CAT_{c_lbl}"
            key_n = f"NAT_{c_lbl}_{n_lbl}"
            key_e = f"ELM_{c_lbl}_{n_lbl}_{e_lbl}"

            base_color = "#00F3FF" if "CORRENTES" in c_lbl else "#00FF99"
            
            i_root = node_map["ROOT"]
            i_c = add_node(key_c, c_lbl, base_color)
            i_n = add_node(key_n, n_lbl, base_color)
            i_e = add_node(key_e, e_lbl, base_color)

            links.append({'source': i_root, 'target': i_c, 'value': v, 'color': 'rgba(255,255,255,0.1)'})
            links.append({'source': i_c,    'target': i_n, 'value': v, 'color': 'rgba(0, 243, 255, 0.2)' if "CORRENTES" in c_lbl else 'rgba(0, 255, 153, 0.2)'})
            links.append({'source': i_n,    'target': i_e, 'value': v, 'color': 'rgba(50,50,50, 0.3)'})

        df_links = pd.DataFrame(links)
        df_links_agg = df_links.groupby(['source', 'target', 'color'])['value'].sum().reset_index()

        final_labels = []
        for i, n in enumerate(nodes):
            val_in = df_links_agg[df_links_agg['target'] == i]['value'].sum()
            if val_in == 0: val_in = df_links_agg[df_links_agg['source'] == i]['value'].sum()
            val_fmt = f"R$ {val_in/1e6:,.1f}M" if val_in > 1e6 else f"R$ {val_in:,.0f}"
            final_labels.append(f"<span style='font-size:13px'>{n['label']}</span><br><span style='font-size:11px; opacity:0.8'>{val_fmt}</span>")

        fig_sankey = go.Figure(data=[go.Sankey(
            node = dict(
                pad = 20, thickness = 10, line = dict(color = "black", width = 0.5),
                label = final_labels, color = [n['color'] for n in nodes],
                x = [0.01 if i==0 else None for i in range(len(nodes))] 
            ),
            link = dict(
                source = df_links_agg['source'], target = df_links_agg['target'],
                value = df_links_agg['value'], color = df_links_agg['color']
            ),
            textfont = dict(family="Orbitron", size=12, color="white")
        )])

        fig_sankey.update_layout(
            title="Decomposição Encadeada da Despesa", height=altura_dinamica, autosize=True,
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=12),
            margin=dict(t=40, b=40, l=10, r=10)
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.warning("Colunas necessárias para o fluxo não encontradas.")   
        
    # Detalhamento: Correntes vs Capital
    st.subheader("⚖️ Detalhamento: Correntes vs Capital")
    st.caption("Explosão hierárquica separada por categoria econômica")
    box_educativo("Classificação Econômica", ["correntes_desp", "capital_desp"])

    c_tree1, c_tree2, c_tree3 = st.columns([1, 1, 2])
    with c_tree1:
        tipo_tree_split = st.radio("Estilo:", ["Treemap (Blocos)", "Sunburst (Solar)"], horizontal=True, key="radio_split_type")
    with c_tree2:
        zoom_split = st.slider("Profundidade:", 1, 4, 2, key="slider_zoom_split", help="Nível de detalhe da hierarquia")
    with c_tree3:
        min_val_split = st.slider("Ocultar valores menores que:", 0, 2000000, 100000, step=100000, format="R$ %d", key="slider_val_split")

    if 'desc_categoria' in desp_ano.columns:
        df_split = desp_ano.copy()
        df_split['desc_categoria'] = df_split['desc_categoria'].fillna("OUTROS")
        
        df_correntes = df_split[df_split['desc_categoria'].str.contains("CORRENTES", case=False, na=False)]
        df_capital = df_split[df_split['desc_categoria'].str.contains("CAPITAL", case=False, na=False)]
        
        path_split = ['desc_funcao', 'desc_natureza', 'desc_elemento']
        path_valid = [c for c in path_split if c in df_split.columns]

        if path_valid:
            def criar_arvore_categoria(df_input, titulo, cor_escala):
                df_f = df_input[df_input['valor_realizado'] >= min_val_split]
                if df_f.empty: return None
                
                if tipo_tree_split == "Treemap (Blocos)":
                    fig = px.treemap(
                        df_f, path=path_valid, values='valor_realizado',
                        color='valor_realizado', color_continuous_scale=cor_escala,
                        maxdepth=zoom_split, title=titulo
                    )
                else:
                    fig = px.sunburst(
                        df_f, path=path_valid, values='valor_realizado',
                        color='valor_realizado', color_continuous_scale=cor_escala,
                        maxdepth=zoom_split, title=titulo
                    )
                
                fig.update_layout(
                    margin=dict(t=40, l=0, r=0, b=0), height=500, template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=12)
                )
                fig.update_traces(textinfo="label+percent entry")
                return fig

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("#### 🔵 Despesas Correntes")
                st.caption(f"Total: {formatar_br(df_correntes['valor_realizado'].sum())}")
                fig_corr = criar_arvore_categoria(df_correntes, "", "Teal")
                if fig_corr: st.plotly_chart(fig_corr, use_container_width=True)
                else: st.info("Sem dados visíveis para este filtro.")

            with col_c2:
                st.markdown("#### 🟢 Despesas de Capital")
                st.caption(f"Total: {formatar_br(df_capital['valor_realizado'].sum())}")
                fig_cap = criar_arvore_categoria(df_capital, "", "Greens")
                if fig_cap: st.plotly_chart(fig_cap, use_container_width=True)
                else: st.info("Sem dados visíveis para este filtro.")
        else:
            st.error("Colunas de hierarquia (Função/Natureza) ausentes nos dados.")
    
    st.markdown("---")       

    # Sub-navegação do Módulo de Despesas
    modo_despesa = st.radio("Modo de Visualização", options=["VISÃO MACRO", "VISÃO DETALHADA", "COMPARADOR AVANÇADO"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- ABA 1: VISÃO MACRO (Despesas) ---
    if modo_despesa == "VISÃO MACRO":
        
        # Tratamento para garantir integridade dos gráficos
        cols_hierarquia = ['desc_funcao', 'nome_orgao', 'desc_categoria', 'desc_natureza', 'desc_elemento']
        for c in cols_hierarquia:
            if c in desp_ano.columns:
                desp_ano[c] = desp_ano[c].fillna("NÃO INFORMADO")

        # 1. Gráfico de Evolução Mensal
        st.subheader("Evolução Temporal da Despesa Paga")
        desp_ano['mes_num'] = pd.to_numeric(desp_ano['mes'], errors='coerce')
        evolucao_mensal = desp_ano.groupby(['mes_num', 'mes'])['valor_realizado'].sum().reset_index().sort_values('mes_num')
        
        fig_line = px.line(evolucao_mensal, x='mes', y='valor_realizado', markers=True, title="Tendência de Pagamentos (Mês a Mês)")
        fig_line.update_traces(line_color='#00F3FF', line_width=3, marker_size=8)
        fig_line.update_layout(height=350, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#333', title="Valor Pago (R$)"))
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("---")

        # 2. Decomposição Hierárquica (Treemap)
        st.subheader(f"Decomposição da Despesa ({lbl_analise} $\\to$ Elemento)")
        
        guia_visual("""
        **Mapa de Árvore (Treemap):**
        * **Tamanho do Retângulo:** Representa o valor gasto. Quanto maior, mais dinheiro consumiu.
        * **Agrupamento:** Os retângulos menores estão aninhados dentro de grupos maiores.
        * **Interatividade:** Clique em um retângulo grande para dar **Zoom** e ver o que tem dentro.
        """)
        
        c_vis1, c_vis2, c_vis3 = st.columns([1, 1, 2])
        with c_vis1:
            tipo_grafico = st.radio("Visualização:", ["Retangular", "Solar"], horizontal=True, label_visibility="collapsed")
        with c_vis2:
            nivel_zoom = st.slider("🔍 Nível de Detalhe (Zoom):", min_value=1, max_value=5, value=2)
        with c_vis3:
            val_min = st.slider("🧹 Filtro de Ruído (Ocultar < R$):", min_value=0, max_value=100_000_000, value=0, step=500_000, format="R$ %d")

        if criterio == "POR FUNÇÃO":
            path_treemap = ['desc_funcao', 'nome_orgao', 'desc_categoria', 'desc_natureza', 'desc_elemento']
        else:
            path_treemap = ['nome_orgao', 'desc_funcao', 'desc_categoria', 'desc_natureza', 'desc_elemento']
            
        path_final = [c for c in path_treemap if c in desp_ano.columns]

        if path_final:
            df_tree_clean = desp_ano[desp_ano['valor_realizado'] >= val_min]
            
            if not df_tree_clean.empty:
                if tipo_grafico == "Retangular":
                    fig_decomp = px.treemap(
                        df_tree_clean, path=path_final, values='valor_realizado',
                        color='valor_realizado', color_continuous_scale='Mint',
                        maxdepth=nivel_zoom, hover_data={'valor_realizado': ':.2f'}
                    )
                    fig_decomp.update_traces(marker=dict(line=dict(color='#000000', width=0.5)), textinfo="label+percent entry")
                else:
                    fig_decomp = px.sunburst(
                        df_tree_clean, path=path_final, values='valor_realizado',
                        color='valor_realizado', color_continuous_scale='Mint', maxdepth=nivel_zoom
                    )
                    fig_decomp.update_traces(textinfo="label+percent entry", insidetextorientation='radial')

                fig_decomp.update_layout(height=750, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=14), margin=dict(t=30, l=0, r=0, b=10))
                st.plotly_chart(fig_decomp, use_container_width=True)
                
                # Feedback sobre filtros
                ocultos = len(desp_ano) - len(df_tree_clean)
                val_oculto = desp_ano[desp_ano['valor_realizado'] < val_min]['valor_realizado'].sum()
                if ocultos > 0:
                    st.caption(f"ℹ️ Visualização filtrada: {ocultos} registros menores ocultos (Totalizando {formatar_br(val_oculto)} fora da visão).")
            else:
                st.warning(f"⚠️ Nenhum registro encontrado acima de R$ {val_min:,.2f}. Tente diminuir o filtro de ruído.")
        else:
            st.warning("Colunas de hierarquia não encontradas.")
        st.markdown("---")

        # 3. Scatter Plot (Orçado vs Pago)
        st.subheader(f"Eficiência: Orçado vs Pago ({lbl_analise})")
        agg_scatter = desp_ano.groupby(col_analise)[['valor_orcado', 'valor_realizado']].sum().reset_index()
        agg_scatter = agg_scatter[agg_scatter['valor_orcado'] > 0]
        
        fig_sc = px.scatter(
            agg_scatter, x='valor_orcado', y='valor_realizado', size='valor_realizado', 
            color=col_analise, hover_name=col_analise, size_max=60,
            labels={'valor_orcado': 'Orçamento Autorizado', 'valor_realizado': 'Valor Pago'}
        )
        if not agg_scatter.empty:
            max_val = agg_scatter['valor_orcado'].max()
            fig_sc.add_shape(type="line", line=dict(dash='dash', color='white', width=1), x0=0, y0=0, x1=max_val, y1=max_val)

        fig_sc.update_layout(height=500, template="plotly_dark", font=dict(family="Orbitron", size=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown("---") 

        # 4. Heatmap de Intensidade
        st.subheader(f"Mapa de Calor: Intensidade de Gastos")
        heat_data = desp_ano.groupby(['mes_num', col_analise])['valor_realizado'].sum().reset_index()
        heat_data.sort_values(by=col_analise, ascending=False, inplace=True)

        fig_heat = px.density_heatmap(heat_data, x='mes_num', y=col_analise, z='valor_realizado', color_continuous_scale='Viridis', nbinsx=12)
        fig_heat.update_layout(height=600, template="plotly_dark", font=dict(family="Orbitron"), paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(dtick=1, title="Mês do Exercício"), yaxis=dict(title=None))
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- ABA 2: VISÃO DETALHADA (Despesas) ---
    elif modo_despesa == "VISÃO DETALHADA":
        st.markdown("### 💠 Deep Dive: Análise Focada")
        
        lista_itens = sorted(desp_ano[col_analise].unique())
        if not lista_itens:
            st.warning("Sem dados para os filtros atuais.")
            st.stop()
            
        col_sel, col_stats = st.columns([1, 3])
        with col_sel:
            escolha = st.selectbox(f"Selecione {lbl_analise}:", lista_itens)
            
        df_foco = desp_ano[desp_ano[col_analise] == escolha]
        
        # Estatísticas contextuais
        total_geral_ano = desp_ano['valor_realizado'].sum()
        total_foco = df_foco['valor_realizado'].sum()
        perc_do_total = (total_foco / total_geral_ano) * 100 if total_geral_ano > 0 else 0
        
        ranking_df = desp_ano.groupby(col_analise)['valor_realizado'].sum().sort_values(ascending=False).reset_index()
        try:
            rank_pos = ranking_df[ranking_df[col_analise] == escolha].index[0] + 1
            total_itens = len(ranking_df)
            txt_rank = f"#{rank_pos} de {total_itens}"
        except:
            txt_rank = "-"

        with col_stats:
            c_s1, c_s2, c_s3 = st.columns(3)
            c_s1.metric("📊 Relevância no Orçamento", f"{perc_do_total:.1f}%", help=f"Quanto {escolha} representa do total do município.")
            c_s2.metric("🏆 Ranking de Gastos", txt_rank, help=f"Posição no ranking de maiores gastos por {lbl_analise}")
            projs_ativos = df_foco[df_foco['valor_realizado'] > 0]['desc_elemento'].nunique()
            c_s3.metric("🏗️ Elementos Ativos", projs_ativos, help="Quantidade de tipos de despesas executadas.")

        st.markdown("---")

        # Painel Executivo (KPIs da Seleção)
        st.subheader(f"📟 Painel Executivo: {escolha}")
        v_orc_f = df_foco['valor_orcado'].sum()
        v_emp_f = df_foco['valor_empenhado'].sum()
        v_liq_f = df_foco['valor_liquidado'].sum()
        v_pag_f = df_foco['valor_realizado'].sum()
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("ORÇADO", formatar_br(v_orc_f), border=True)
        k2.metric("EMPENHADO", formatar_br(v_emp_f), delta=f"{(v_emp_f/v_orc_f*100):.1f}% do Orc" if v_orc_f else "0%", border=True)
        k3.metric("LIQUIDADO", formatar_br(v_liq_f), delta=f"{(v_liq_f/v_emp_f*100):.1f}% do Emp" if v_emp_f else "0%", border=True)
        k4.metric("PAGO", formatar_br(v_pag_f), delta=f"{(v_pag_f/v_liq_f*100):.1f}% do Liq" if v_liq_f else "0%", border=True)
        
        st.plotly_chart(plot_gauge(v_pag_f, v_orc_f, f"Taxa de Execução Orçamentária ({escolha})"), use_container_width=True)
        st.markdown("---")

        # Ranking Interno (Drill-down)
        st.subheader("🏆 Maiores Despesas deste Setor")
        c_rank_det1, c_rank_det2 = st.columns([1, 3])
        with c_rank_det1:
            qtd_top_det = st.slider("Qtd. Itens:", 5, 20, 5, key="slider_rank_detalhe")
        
        df_rank_foco = df_foco.groupby('desc_elemento')['valor_realizado'].sum().reset_index()
        df_rank_foco = df_rank_foco.sort_values(by='valor_realizado', ascending=False).head(qtd_top_det)
        df_rank_foco['label_txt'] = df_rank_foco['valor_realizado'].apply(lambda x: f"R$ {x/1e6:.1f}M" if x >= 1e6 else f"R$ {x:,.0f}")

        fig_bar_det = px.bar(df_rank_foco, x='valor_realizado', y='desc_elemento', orientation='h', text='label_txt')
        fig_bar_det.update_traces(marker_color='#00F3FF', marker_line_color='#FFFFFF', marker_line_width=1, textposition='outside', cliponaxis=False)
        fig_bar_det.update_layout(yaxis=dict(autorange="reversed", title=None), xaxis=dict(showgrid=True, gridcolor='#333', title="Valor Pago"), height=max(300, qtd_top_det * 40), template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=12), margin=dict(l=0, r=50, t=10, b=10))
        st.plotly_chart(fig_bar_det, use_container_width=True)
        st.markdown("---")

        # Correntes vs Capital (Focado)
        st.subheader("⚖️ Detalhamento: Correntes vs Capital")
        if 'desc_categoria' in df_foco.columns:
            df_corr_f = df_foco[df_foco['desc_categoria'].str.contains("CORRENTES", case=False, na=False)]
            df_cap_f = df_foco[df_foco['desc_categoria'].str.contains("CAPITAL", case=False, na=False)]
            
            c_split1, c_split2 = st.columns(2)
            
            def plot_tree_simple(df_in, color_scale):
                if df_in.empty: return None
                fig = px.treemap(df_in, path=['desc_natureza', 'desc_elemento'], values='valor_realizado', color='valor_realizado', color_continuous_scale=color_scale)
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0,l=0,r=0,b=0), height=300)
                return fig

            with c_split1:
                st.markdown(f"**🔵 Despesas Correntes** (R$ {df_corr_f['valor_realizado'].sum()/1e6:,.1f}M)")
                fig_c = plot_tree_simple(df_corr_f, "Teal")
                if fig_c: st.plotly_chart(fig_c, use_container_width=True)
                else: st.info("Sem registros.")

            with c_split2:
                st.markdown(f"**🟢 Despesas de Capital** (R$ {df_cap_f['valor_realizado'].sum()/1e6:,.1f}M)")
                fig_k = plot_tree_simple(df_cap_f, "Greens")
                if fig_k: st.plotly_chart(fig_k, use_container_width=True)
                else: st.info("Sem registros.")
        st.markdown("---")

        # Sunburst e Heatmap
        c_l3_1, c_l3_2 = st.columns([1, 1])
        with c_l3_1:
            st.markdown("#### 🍩 Distribuição Interativa")
            st.caption("Clique nas fatias para expandir os níveis (Categoria ➝ Natureza)")
            if 'desc_categoria' in df_foco.columns and 'desc_natureza' in df_foco.columns:
                df_sun = df_foco.groupby(['desc_categoria', 'desc_natureza'])['valor_realizado'].sum().reset_index()
                fig_sun = px.sunburst(df_sun, path=['desc_categoria', 'desc_natureza'], values='valor_realizado', color='valor_realizado', color_continuous_scale='GnBu')
                fig_sun.update_traces(textinfo='label+percent entry')
                fig_sun.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, b=0, l=0, r=0), height=350)
                st.plotly_chart(fig_sun, use_container_width=True)
            else:
                st.info("Dados hierárquicos indisponíveis.")

        with c_l3_2:
            st.markdown("#### 📅 Sazonalidade (Heatmap)")
            if 'desc_natureza' in df_foco.columns:
                heat_foco = df_foco.groupby(['mes', 'desc_natureza'])['valor_realizado'].sum().reset_index()
                heat_foco['mes_num'] = pd.to_numeric(heat_foco['mes'], errors='coerce')
                heat_foco.sort_values('mes_num', inplace=True)
                
                fig_heat_f = px.density_heatmap(heat_foco, x='mes', y='desc_natureza', z='valor_realizado', color_continuous_scale='Tealgrn', nbinsx=12)
                fig_heat_f.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(title=None, tickfont=dict(size=10)), xaxis=dict(title=None), coloraxis_showscale=False, height=350, margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig_heat_f, use_container_width=True)
        st.markdown("---")

        # Cadeia de Composição (Focada)
        st.subheader("🔗 Cadeia de Composição (Detalhada)")
        st.caption("Fluxo: Natureza da Despesa ➝ Elemento (Onde o dinheiro finaliza)")
        
        qtd_sankey_det = st.slider("Quantidade de Elementos na Ponta:", 5, 50, 10, key="slider_sankey_det")
        cols_sankey_foco = ['desc_natureza', 'desc_elemento']
        if all(c in df_foco.columns for c in cols_sankey_foco):
            df_sk_f = df_foco.groupby(cols_sankey_foco)['valor_realizado'].sum().reset_index()
            top_el_f = df_sk_f.groupby('desc_elemento')['valor_realizado'].sum().nlargest(qtd_sankey_det).index
            df_sk_f = df_sk_f[df_sk_f['desc_elemento'].isin(top_el_f)]
            
            all_nodes = list(pd.concat([df_sk_f['desc_natureza'], df_sk_f['desc_elemento']]).unique())
            map_nodes = {n: i for i, n in enumerate(all_nodes)}
            height_sk = max(400, len(top_el_f) * 30)

            fig_sk_f = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=10, line=dict(color="black", width=0.5), label=[f"{n}" for n in all_nodes], color="#00F3FF"),
                link=dict(source=df_sk_f['desc_natureza'].map(map_nodes), target=df_sk_f['desc_elemento'].map(map_nodes), value=df_sk_f['valor_realizado'], color='rgba(0, 243, 255, 0.2)')
            )])
            fig_sk_f.update_layout(height=height_sk, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=11), title_text=None, margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_sk_f, use_container_width=True)
        st.markdown("---")

        # Tabela de Dados Granulares
        st.subheader("🕵️‍♀️ Dados Granulares (Detalhamento)")
        with st.expander("Filtros Avançados da Tabela", expanded=False):
            ft_col1, ft_col2 = st.columns(2)
            with ft_col1:
                search_term = st.text_input("Buscar por Elemento ou Credor:", placeholder="Ex: Material, Obras...")
            with ft_col2:
                min_table_val = st.number_input("Valor Mínimo (R$):", value=0, step=1000)

        cols_tab = ['mes', 'desc_elemento', 'valor_orcado', 'valor_empenhado', 'valor_liquidado', 'valor_realizado']
        df_tab = df_foco[cols_tab].copy()
        
        df_tab = df_tab[df_tab['valor_realizado'] >= min_table_val]
        if search_term:
            df_tab = df_tab[df_tab['desc_elemento'].str.contains(search_term, case=False, na=False)]
            
        df_tab.sort_values('valor_realizado', ascending=False, inplace=True)
        
        st.dataframe(
            df_tab,
            column_config={
                "mes": "Mês",
                "desc_elemento": "Descrição da Despesa",
                "valor_orcado": st.column_config.NumberColumn("Orçado", format="R$ %.2f"),
                "valor_empenhado": st.column_config.NumberColumn("Empenhado", format="R$ %.2f"),
                "valor_liquidado": st.column_config.NumberColumn("Liquidado", format="R$ %.2f"),
                "valor_realizado": st.column_config.ProgressColumn(
                    "Pago (Realizado)", format="R$ %.2f", min_value=0, max_value=df_tab['valor_realizado'].max() if not df_tab.empty else 1000
                )
            },
            hide_index=True, use_container_width=True, height=400
        )

    # --- ABA 3: COMPARADOR (Despesas) ---
    else:
        lista_completa = sorted(desp_ano[col_analise].unique())
        selecao = st.multiselect(f"Comparar {lbl_analise}s:", lista_completa, default=lista_completa[:2] if len(lista_completa)>1 else lista_completa)
        if selecao:
            df_comp = desp_ano[desp_ano[col_analise].isin(selecao)]
            comp_vals = df_comp.groupby(col_analise)[['valor_orcado', 'valor_realizado']].sum().reset_index()
            comp_melt = comp_vals.melt(id_vars=col_analise, value_vars=['valor_orcado', 'valor_realizado'], var_name='Tipo', value_name='Valor')
            
            fig_comp = px.bar(comp_melt, x='Valor', y=col_analise, color='Tipo', barmode='group', color_discrete_map={'valor_orcado': '#555555', 'valor_realizado': '#00F3FF'}, title="Meta (Orçado) vs Realidade (Pago)")
            fig_comp.update_layout(template="plotly_dark", font=dict(family="Orbitron"), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            fig_sc_comp = px.scatter(df_comp, x='valor_orcado', y='valor_realizado', color=col_analise, size='valor_realizado', title="Dispersão das Despesas Selecionadas")
            fig_sc_comp.update_layout(template="plotly_dark", font=dict(family="Orbitron"), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_sc_comp, use_container_width=True)

# ==============================================================================
# 10. MÓDULO: APENAS RECEITAS
# ==============================================================================
elif visao_selecionada == "APENAS RECEITAS":
    st.header(f"Análise de Receitas - {label_ano_titulo}")
    
    t_real_rec = rec_ano['valor_realizado'].sum()
    qtd_meses = rec_ano['mes'].nunique()
    media_mensal = t_real_rec / qtd_meses if qtd_meses > 0 else 0

    col_r1, col_r2 = st.columns(2)
    with st.expander("📖 Glossário de Receitas e Siglas", expanded=False):
        col_glos1, col_glos2 = st.columns(2)
        with col_glos1:
            st.markdown("**Conceitos Gerais:**")
            st.markdown(f"• {obter_conceito('receita_corrente')}")
            st.markdown(f"• {obter_conceito('receita_capital')}")
        with col_glos2:
            st.markdown("**Principais Impostos e Fundos:**")
            st.markdown(f"• {obter_conceito('iptu')}")
            st.markdown(f"• {obter_conceito('iss')}")
            st.markdown(f"• {obter_conceito('fundeb')}")
    
    col_r1.metric("TOTAL ARRECADADO", formatar_br(t_real_rec))
    col_r2.metric("MÉDIA MENSAL", formatar_br(media_mensal), help="Arrecadação total dividida pelos meses com registro.")
    st.markdown("---")

    modo_receita = st.radio("Modo de Visualização", options=["VISÃO MACRO", "VISÃO DETALHADA"], horizontal=True, key="radio_modo_rec")
    st.markdown("<br>", unsafe_allow_html=True)

    # Preparação para uso em todas as abas
    rec_ano['mes_num'] = pd.to_numeric(rec_ano['mes'], errors='coerce')
    cols_hierarquia_rec = ['nome_origem', 'nome_especie', 'nome_tipo']
    for c in cols_hierarquia_rec:
        if c in rec_ano.columns:
            rec_ano[c] = rec_ano[c].fillna("NÃO CLASSIFICADO")

    # --- ABA 1: VISÃO MACRO (Receitas) ---
    if modo_receita == "VISÃO MACRO":
        
        st.subheader("Evolução da Arrecadação Mensal")
        guia_visual("""
        Acompanhe a entrada de recursos mês a mês.
        * **Sazonalidade do IPTU:** É comum ver um pico muito alto em **Janeiro/Fevereiro** devido ao pagamento antecipado do IPTU.
        **Estabilidade:** Receitas como ISS tendem a ser mais estáveis, flutuando com a economia.
        """)
        
        evolucao_rec = rec_ano.groupby(['mes_num', 'mes'])['valor_realizado'].sum().reset_index().sort_values('mes_num')
        fig_line_rec = px.line(evolucao_rec, x='mes', y='valor_realizado', markers=True, title="Tendência de Entradas (Mês a Mês)")
        fig_line_rec.update_traces(line_color='#00FF99', line_width=3, marker_size=8)
        fig_line_rec.update_layout(height=350, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#333', title="Valor Arrecadado"))
        st.plotly_chart(fig_line_rec, use_container_width=True)
        st.markdown("---")

        # Decomposição Hierárquica
        st.subheader(f"Origem do Dinheiro (Origem $\\to$ Espécie $\\to$ Tipo)")
        c_vis_r1, c_vis_r2, c_vis_r3 = st.columns([1, 1, 2])
        with c_vis_r1:
            tipo_grafico_rec = st.radio("Visualização:", ["Retangular", "Solar"], horizontal=True, key="rad_vis_rec", label_visibility="collapsed")
        with c_vis_r2:
            zoom_rec = st.slider("🔍 Zoom:", 1, 3, 2, key="slider_zoom_rec")
        with c_vis_r3:
            val_min_rec = st.slider("🧹 Filtro de Ruído (< R$):", 0, 5000000, 0, step=100000, format="R$ %d", key="slider_noise_rec")

        df_tree_rec = rec_ano[rec_ano['valor_realizado'] >= val_min_rec]
        path_rec = [c for c in cols_hierarquia_rec if c in df_tree_rec.columns]
        
        if not df_tree_rec.empty and path_rec:
            if tipo_grafico_rec == "Retangular":
                fig_decomp_rec = px.treemap(
                    df_tree_rec, path=path_rec, values='valor_realizado',
                    color='valor_realizado', color_continuous_scale='Emrld', maxdepth=zoom_rec
                )
                fig_decomp_rec.update_traces(marker=dict(line=dict(color='#000000', width=0.5)), textinfo="label+percent entry")
            else:
                fig_decomp_rec = px.sunburst(
                    df_tree_rec, path=path_rec, values='valor_realizado',
                    color='valor_realizado', color_continuous_scale='Emrld', maxdepth=zoom_rec
                )
                fig_decomp_rec.update_traces(textinfo="label+percent entry")
            
            fig_decomp_rec.update_layout(height=700, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=14), margin=dict(t=30, l=0, r=0, b=10))
            st.plotly_chart(fig_decomp_rec, use_container_width=True)
        else:
            st.warning("Sem dados suficientes para gerar a hierarquia.")
        st.markdown("---")

        # Ranking de Fontes
        st.subheader("🏆 Top Fontes de Arrecadação")
        c_rank_r1, c_rank_r2 = st.columns([1, 2])
        with c_rank_r1:
            qtd_top_rec = st.slider("Qtd. Itens:", 5, 20, 10, key="sl_top_rec")
        with c_rank_r2:
            nivel_rank_rec = st.radio("Agrupar por:", ["Espécie (Médio)", "Tipo (Detalhado)"], horizontal=True, key="rad_rank_rec")
        
        col_rank_rec = 'nome_especie' if "Espécie" in nivel_rank_rec else 'nome_tipo'
        
        if col_rank_rec in rec_ano.columns:
            df_rank_rec = rec_ano.groupby(col_rank_rec)['valor_realizado'].sum().reset_index()
            df_rank_rec = df_rank_rec.sort_values('valor_realizado', ascending=False).head(qtd_top_rec)
            df_rank_rec['label_txt'] = df_rank_rec['valor_realizado'].apply(lambda x: f"R$ {x/1e6:.1f}M" if x >= 1e6 else f"R$ {x:,.0f}")
            
            fig_bar_rec = px.bar(df_rank_rec, x='valor_realizado', y=col_rank_rec, orientation='h', text='label_txt')
            fig_bar_rec.update_traces(marker_color='#00FF99', marker_line_color='#FFFFFF', marker_line_width=1, textposition='outside', cliponaxis=False)
            fig_bar_rec.update_layout(yaxis=dict(autorange="reversed", title=None), xaxis=dict(showgrid=True, gridcolor='#333', title="Valor Arrecadado"), height=max(400, qtd_top_rec * 40), template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron"))
            st.plotly_chart(fig_bar_rec, use_container_width=True)
        st.markdown("---")

        # Sankey de Receita (Fluxo)
        st.subheader("🔗 Fluxo de Entrada: Origem $\\to$ Destino")
        qtd_sankey_rec = st.slider("Detalhe do Fluxo (Top Tipos):", 5, 50, 15, key="sl_sankey_rec")
        
        df_sk_rec = rec_ano.copy()
        if 'nome_tipo' in df_sk_rec.columns:
            top_tipos_rec = df_sk_rec.groupby('nome_tipo')['valor_realizado'].sum().nlargest(qtd_sankey_rec).index
            df_sk_rec = df_sk_rec[df_sk_rec['nome_tipo'].isin(top_tipos_rec)]
            
            df_agg_sk = df_sk_rec.groupby(cols_hierarquia_rec)['valor_realizado'].sum().reset_index()
            
            nodes_r = []
            links_r = []
            node_map_r = {}
            
            def add_node_r(key, label, color="rgba(0, 255, 153, 0.5)"):
                if key not in node_map_r:
                    node_map_r[key] = len(nodes_r)
                    nodes_r.append({"label": label, "color": color})
                return node_map_r[key]

            add_node_r("ROOT", "RECEITA TOTAL", "#FFFFFF")
            
            for _, row in df_agg_sk.iterrows():
                v = row['valor_realizado']
                orig = row['nome_origem']
                esp = row['nome_especie']
                tip = row['nome_tipo']
                
                i_root = node_map_r["ROOT"]
                i_orig = add_node_r(f"O_{orig}", orig, "#00FF99")
                i_esp = add_node_r(f"E_{esp}", esp, "#00CC88")
                i_tip = add_node_r(f"T_{tip}", tip, "#009977")
                
                links_r.append({'source': i_root, 'target': i_orig, 'value': v, 'color': 'rgba(255,255,255,0.1)'})
                links_r.append({'source': i_orig, 'target': i_esp, 'value': v, 'color': 'rgba(0, 255, 153, 0.2)'})
                links_r.append({'source': i_esp,  'target': i_tip,  'value': v, 'color': 'rgba(0, 204, 136, 0.2)'})
                
            df_l_rec = pd.DataFrame(links_r).groupby(['source', 'target', 'color'])['value'].sum().reset_index()
            
            final_labels_r = []
            for i, n in enumerate(nodes_r):
                val_in = df_l_rec[df_l_rec['target'] == i]['value'].sum()
                if val_in == 0: val_in = df_l_rec[df_l_rec['source'] == i]['value'].sum()
                val_fmt = f"R$ {val_in/1e6:,.1f}M" if val_in > 1e6 else f"R$ {val_in:,.0f}"
                final_labels_r.append(f"<span style='font-size:13px'>{n['label']}</span><br><span style='font-size:11px; opacity:0.8'>{val_fmt}</span>")

            fig_sk_r = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=10, line=dict(color="black", width=0.5), label=final_labels_r, color=[n['color'] for n in nodes_r]),
                link=dict(source=df_l_rec['source'], target=df_l_rec['target'], value=df_l_rec['value'], color=df_l_rec['color'])
            )])
            fig_sk_r.update_layout(title="Decomposição da Receita", height=max(600, len(top_tipos_rec)*30), template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Orbitron", size=12))
            st.plotly_chart(fig_sk_r, use_container_width=True)
        st.markdown("---")
        
        # Ranking Final
        st.subheader("📊 Ranking Final por Tipo de Receita")
        top_r = rec_ano.groupby('nome_tipo')['valor_realizado'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_rank_final = px.bar(top_r, x='valor_realizado', y='nome_tipo', orientation='h', text_auto='.2s')
        fig_rank_final.update_traces(marker_color='#00F3FF')
        fig_rank_final.update_layout(yaxis=dict(autorange="reversed", title=None), xaxis=dict(title="Total Arrecadado"), template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", title="Top 10 Tipos de Arrecadação")
        st.plotly_chart(fig_rank_final, use_container_width=True)

    # --- ABA 2: VISÃO DETALHADA (Receitas) ---
    elif modo_receita == "VISÃO DETALHADA":
        
        st.markdown("### 💠 Deep Dive: Análise de Fonte de Receita")
        
        lista_origens = sorted(rec_ano['nome_origem'].unique())
        sel_origem = st.selectbox("Selecione a Origem da Receita:", lista_origens)
        df_foco_rec = rec_ano[rec_ano['nome_origem'] == sel_origem]
        
        total_origem = df_foco_rec['valor_realizado'].sum()
        perc_total = (total_origem / t_real_rec * 100) if t_real_rec > 0 else 0
        
        c_ctx1, c_ctx2 = st.columns([1, 3])
        with c_ctx1:
            st.metric("Total da Origem", formatar_br(total_origem))
        with c_ctx2:
            st.metric("Representatividade", f"{perc_total:.1f}% do Total Arrecadado")
            # Tratamento para barra de progresso (evita erros com valores negativos ou > 100%)
            val_barra = max(0.0, min(1.0, perc_total / 100))
            st.progress(val_barra)
        st.markdown("---")
        
        # Composição e Sazonalidade
        c_det_r1, c_det_r2 = st.columns(2)
        with c_det_r1:
            st.markdown("#### Composição Interna (Espécie $\\to$ Tipo)")
            if not df_foco_rec.empty:
                fig_sun_foco = px.sunburst(df_foco_rec, path=['nome_especie', 'nome_tipo'], values='valor_realizado', color='valor_realizado', color_continuous_scale='Greens')
                fig_sun_foco.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=400)
                st.plotly_chart(fig_sun_foco, use_container_width=True)
                
        with c_det_r2:
            st.markdown("#### Sazonalidade desta Origem")
            heat_foco_rec = df_foco_rec.groupby(['mes_num', 'nome_especie'])['valor_realizado'].sum().reset_index()
            fig_heat_fr = px.density_heatmap(heat_foco_rec, x='mes_num', y='nome_especie', z='valor_realizado', color_continuous_scale='Greens', nbinsx=12)
            fig_heat_fr.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=400, xaxis=dict(dtick=1, title="Mês"))
            st.plotly_chart(fig_heat_fr, use_container_width=True)
        st.markdown("---")
        
        # Tabela Detalhada com Tratamento de Exceções
        st.subheader("🕵️‍♀️ Registros Detalhados")
        cols_tab_rec = ['mes', 'nome_especie', 'nome_tipo', 'valor_realizado']
        
        if not df_foco_rec.empty:
            v_real_max = df_foco_rec['valor_realizado'].max()
            v_real_min = df_foco_rec['valor_realizado'].min()
            
            # Tratamento seguro para range da barra (lida com deduções negativas)
            safe_min = float(min(0, v_real_min))
            safe_max = float(max(1.0, v_real_max))
            if safe_max <= safe_min: safe_max = safe_min + 1.0 
        else:
            safe_min, safe_max = 0.0, 1.0

        st.dataframe(
            df_foco_rec[cols_tab_rec].sort_values('valor_realizado', ascending=False),
            column_config={
                "valor_realizado": st.column_config.ProgressColumn(
                    "Arrecadado", format="R$ %.2f", min_value=safe_min, max_value=safe_max
                )
            },
            use_container_width=True, hide_index=True
        )