import pandas as pd
import glob
import os

# ==============================================================================
# 1. FUNÇÕES AUXILIARES DE TRATAMENTO
# ==============================================================================
def limpar_moeda(valor):
    """
    Converte strings no formato monetário brasileiro (ex: '1.000,00') para float Python.
    Trata valores nulos e vazios, retornando 0.0 em caso de erro.
    """
    if pd.isna(valor) or valor == '':
        return 0.0
    valor_str = str(valor).strip()
    
    # Remove separador de milhar (.) e substitui decimal (,) por ponto
    if ',' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return 0.0

# ==============================================================================
# 2. PROCESSO DE UNIFICAÇÃO DOS ARQUIVOS DE DESPESA
# ==============================================================================
pasta_origem = r'C:\Users\lucas\Desktop\tcc_dashboard_poa\data\despesas'
arquivo_saida = os.path.join(pasta_origem, 'despesas_unificado.csv')
padrao = os.path.join(pasta_origem, '*.csv')
arquivos = glob.glob(padrao)

# Define as colunas monetárias que precisam de conversão específica
conversores = {
    'vlpag': limpar_moeda, 
    'vlorcini': limpar_moeda,
    'vlemp': limpar_moeda,
    'vlliq': limpar_moeda
}

lista_dfs = []
print(f"--- Iniciando Unificação ({len(arquivos)} arquivos) ---")

for arquivo in arquivos:
    # Evita ler o próprio arquivo de saída se ele já existir na pasta
    if arquivo == arquivo_saida:
        continue
    try:
        # Tenta leitura padrão UTF-8
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', converters=conversores)
    except:
        try:
            # Fallback para Latin1 (comum em dados governamentais antigos)
            df = pd.read_csv(arquivo, sep=';', encoding='latin1', converters=conversores)
        except Exception as e:
            print(f"Erro em {arquivo}: {e}")
            continue
    lista_dfs.append(df)

if lista_dfs:
    df_final = pd.concat(lista_dfs, ignore_index=True)
    try:
        # Exporta o dataset consolidado mantendo o padrão brasileiro de decimal
        df_final.to_csv(arquivo_saida, index=False, sep=';', encoding='utf-8', decimal=',')
        print(f"✅ Arquivo unificado salvo com sucesso!")
    except PermissionError:
        print("⚠️ Feche o arquivo no Excel e tente novamente!")
        exit()
else:
    print("Nenhum arquivo encontrado.")

# ==============================================================================
# 3. EXTRAÇÃO, TRANSFORMAÇÃO E LIMPEZA (ETL)
# ==============================================================================
print("\n--- Carregando para Análise ---")

base_path = r'C:\Users\lucas\Desktop\tcc_dashboard_poa\data'
caminho_receita = os.path.join(base_path, 'receitas', 'receita.csv')
caminho_despesa = arquivo_saida 

anos_foco = [2019, 2020, 2021, 2022, 2023]

# --- 3.1 Tratamento de Receitas ---
try:
    df_receita = pd.read_csv(caminho_receita, sep=';', encoding='utf-8', 
                             converters={'valor_arrecadado': limpar_moeda, 'valor_orcado': limpar_moeda})
except:
    df_receita = pd.read_csv(caminho_receita, sep=';', encoding='latin1', 
                             converters={'valor_arrecadado': limpar_moeda, 'valor_orcado': limpar_moeda})

# --- 3.2 Tratamento de Despesas (Arquivo Unificado) ---
df_despesa = pd.read_csv(caminho_despesa, sep=';', encoding='utf-8', decimal=',')

# --- 3.3 Padronização e Filtragem (Receitas) ---
if 'df_receita' in locals():
    cols_rec = ['ano', 'mes', 'nome_origem', 'nome_especie', 'nome_tipo', 'valor_arrecadado', 'valor_orcado']
    cols_existentes = [c for c in cols_rec if c in df_receita.columns]
    
    df_receita = df_receita[cols_existentes].copy()
    df_receita.rename(columns={'ano': 'ano_exercicio', 'valor_arrecadado': 'valor_realizado'}, inplace=True)
    
    # Filtro temporal e marcação de tipo
    df_receita = df_receita[df_receita['ano_exercicio'].isin(anos_foco)]
    df_receita['tipo_conta'] = 'Receita'

# --- 3.4 Padronização e Filtragem (Despesas) ---
    # Seleção de colunas de interesse (incluindo hierarquia orçamentária)
    cols_desp = [
        'exercicio', 'mes', 'nome_orgao', 'desc_funcao', 'desc_elemento', 
        'desc_categoria', 'desc_natureza',
        'vlorcini', 'vlpag', 'vlemp', 'vlliq'
    ]
    
    cols_existentes = [c for c in cols_desp if c in df_despesa.columns]
    df_despesa = df_despesa[cols_existentes].copy()
    
    # Renomeação para termos mais claros e padronizados com o app
    df_despesa.rename(columns={
        'exercicio': 'ano_exercicio', 
        'vlpag': 'valor_realizado', 
        'vlorcini': 'valor_orcado',
        'vlemp': 'valor_empenhado',
        'vlliq': 'valor_liquidado'
    }, inplace=True)
    
    # Filtro temporal
    df_despesa = df_despesa[df_despesa['ano_exercicio'].isin(anos_foco)]
    
    # Normalização de strings (Remoção de espaços e Upper Case)
    if 'desc_funcao' in df_despesa.columns:
        df_despesa['desc_funcao'] = df_despesa['desc_funcao'].astype(str).str.strip().str.upper()
    if 'nome_orgao' in df_despesa.columns:
        df_despesa['nome_orgao'] = df_despesa['nome_orgao'].astype(str).str.strip().str.upper()
        
    df_despesa['tipo_conta'] = 'Despesa'

print("\n--- Amostra Final ---")
print(df_despesa[['desc_funcao', 'valor_orcado', 'valor_empenhado', 'valor_liquidado', 'valor_realizado']].head())

# ==============================================================================
# 4. PREPARAÇÃO DE DADOS PARA VISUALIZAÇÃO (SANKEY)
# ==============================================================================

# Lógica de Agrupamento: Seleciona Top 5 e agrupa o restante em "OUTROS"
# Isso evita que o gráfico de Sankey fique ilegível com excesso de nós.

# 4.1 Agrupamento de Despesas (Por Função)
total_por_funcao = df_despesa.groupby('desc_funcao')['valor_realizado'].sum().sort_values(ascending=False)
top_5_funcoes = total_por_funcao.head(5).index.tolist()
df_despesa['funcao_sankey'] = df_despesa['desc_funcao'].apply(lambda x: x if x in top_5_funcoes else 'OUTRAS DESPESAS')

# 4.2 Agrupamento de Receitas (Por Tipo)
top_rec = df_receita.groupby('nome_tipo')['valor_realizado'].sum().sort_values(ascending=False).head(5).index.tolist()
df_receita['receita_sankey'] = df_receita['nome_tipo'].apply(lambda x: x if x in top_rec else 'OUTRAS RECEITAS')

# 4.3 Construção do Fluxo (Origem -> Destino)
# Fluxo de Entrada: Fonte de Receita -> Tesouro Municipal
df_entrada = df_receita.groupby(['ano_exercicio', 'receita_sankey'], as_index=False)['valor_realizado'].sum()
df_entrada['source'] = df_entrada['receita_sankey']
df_entrada['target'] = 'Tesouro Municipal'

# Fluxo de Saída: Tesouro Municipal -> Função de Despesa
df_saida = df_despesa.groupby(['ano_exercicio', 'funcao_sankey'], as_index=False)['valor_realizado'].sum()
df_saida['source'] = 'Tesouro Municipal'
df_saida['target'] = df_saida['funcao_sankey']

# 4.4 Consolidação e Exportação
df_fluxo = pd.concat([df_entrada, df_saida], ignore_index=True)
df_fluxo.to_csv(os.path.join(base_path, 'dados_sankey_tcc.csv'), index=False, sep=';', decimal=',')

print("ETL Concluído com sucesso (Global)!")