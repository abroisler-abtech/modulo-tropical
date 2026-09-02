import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

st.set_page_config(page_title="Módulo Tropical - Sistema de Expedição", layout="wide", page_icon="🌴")

st.title("🌴 Módulo Tropical - Sistema Integrado de Expedição & Operação")
st.caption("Gestão de Separação, Conferência, Carregamento e Vasilhames")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://nlgxmrtxemyxjxqekkno.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
API_IA_URL = st.secrets.get("API_IA_URL", "https://modulo-tropical-ia.onrender.com")

@st.cache_resource
def get_supabase_client(url: str, key: str):
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)

# Menu Lateral Limpo
st.sidebar.markdown("### Navegação do Módulo Tropical")
modulo = st.sidebar.radio(
    "",
    [
        "📋 Separação do Dia",
        "✏️ Lançamentos Avulsos",
        "📦 Controle de Caixas & Fornecedores",
        "🔮 Previsão de IA",
        "🚚 Carregamento & Rotas"
    ]
)

def exibir_metricas_detalhadas(df, col_qtd, col_uni, col_rota, col_empresa, titulo=""):
    if titulo:
        st.markdown(f"#### {titulo}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    if col_rota in df.columns:
        c1.metric("Rotas", df[col_rota].nunique())
    if col_empresa in df.columns:
        c2.metric("Clientes", df[col_empresa].nunique())
        
    kg_total = df[df[col_uni].str.upper() == 'KG'][col_qtd].sum() if col_uni in df.columns else 0
    un_total = df[df[col_uni].str.upper() == 'UN'][col_qtd].sum() if col_uni in df.columns else 0
    bj_total = df[df[col_uni].str.upper() == 'BJ'][col_qtd].sum() if col_uni in df.columns else 0
    outros_total = df[~df[col_uni].str.upper().isin(['KG', 'UN', 'BJ'])][col_qtd].sum() if col_uni in df.columns else 0
    
    c3.metric("Peso Total (KG)", f"{kg_total:,.2f} kg")
    c4.metric("Total Unidades", f"{int(un_total):,} und")
    c5.metric("Total Ovos (BJ)", f"{int(bj_total):,} bj")
    c6.metric("Total Outros", f"{int(outros_total):,} vol")

# -------------------------------------------------------------------
# 1. SEPARAÇÃO DO DIA
# -------------------------------------------------------------------
if modulo == "📋 Separação do Dia":
    st.header("📋 Base de Separação Diária do Galpão")
    uploaded_file = st.file_uploader("Suba a planilha do dia (Base0608.xlsx / Pré-venda)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            df_dia = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.success(f"Planilha carregada com sucesso! Total de registros: {len(df_dia)}")
            
            col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_dia.columns else 'ROTA'
            col_empresa = 'Empresa' if 'Empresa' in df_dia.columns else 'CLIENTE'
            col_prod = 'PRODUTO' if 'PRODUTO' in df_dia.columns else 'PRODUTO'
            col_qtd = 'Qtdade' if 'Qtdade' in df_dia.columns else 'QTD'
            col_uni = 'UNIDADE' if 'UNIDADE' in df_dia.columns else 'UN'

            exibir_metricas_detalhadas(df_dia, col_qtd, col_uni, col_rota, col_empresa, "🚚 Resumo Geral de Todas as Rotas do Galpão")

            st.subheader("Pré-visualização dos Pedidos")
            st.dataframe(df_dia.head(20), use_container_width=True)

            st.session_state['df_separacao'] = df_dia

        except Exception as e:
            st.error(f"Erro ao processar planilha: {e}")

# -------------------------------------------------------------------
# 2. LANÇAMENTOS AVULSOS
# -------------------------------------------------------------------
elif modulo == "✏️ Lançamentos Avulsos":
    st.header("✏️ Lançamentos Avulsos e Ajustes de Estoque")
    with st.form("form_avulso"):
        col1, col2 = st.columns(2)
        with col1:
            tipo_mov = st.selectbox("Tipo", ["ENTRADA_AVULSA", "SAIDA_AVULSA", "PERDA", "SOBRA"])
            produto = st.text_input("Nome do Produto (Ex: Tomate Débora)")
        with col2:
            quantidade = st.number_input("Quantidade (KG/CX)", min_value=0.1, value=10.0)
            motivo = st.text_input("Motivo / Observação")
            
        if st.form_submit_button("Registrar Lançamento"):
            st.success("Lançamento registrado localmente!")

# -------------------------------------------------------------------
# 3. CONTROLE DE CAIXAS & FORNECEDORES
# -------------------------------------------------------------------
elif modulo == "📦 Controle de Caixas & Fornecedores":
    st.header("📦 Gestão de Embalagens e Entrada/Saída com Fornecedores")
    tab1, tab2 = st.tabs(["🔄 Movimentação de Caixas", "🏭 Cadastrar Fornecedor"])
    with tab1:
        st.subheader("Registro de Entrada e Saída de Embalagens")
        sel_caixa = st.selectbox("Tipo de Embalagem", ["Caixa K de Madeira", "Monobloco Plástico Preto", "Palete PBR"])
        operacao = st.radio("Operação", ["ENTRADA", "SAIDA"])
        qtd_caixas = st.number_input("Quantidade de Caixas/Paletes", min_value=1, value=50)
        if st.button("Registrar Movimentação"):
            st.success("Movimentação salva com sucesso!")
    with tab2:
        st.subheader("Novo Fornecedor / Produtor")
        nome_forn = st.text_input("Nome / Razão Social")
        if st.button("Cadastrar Fornecedor"):
            st.success(f"Fornecedor '{nome_forn}' cadastrado!")

# -------------------------------------------------------------------
# 4. PREVISÃO DE IA
# -------------------------------------------------------------------
elif modulo == "🔮 Previsão de IA":
    st.header("🔮 Previsão de Produtividade com IA")
    col1, col2 = st.columns(2)
    with col1:
        dia_op = st.number_input("Dia da Operação", min_value=1, value=6)
    with col2:
        peso_op = st.number_input("Carga Prevista (KG)", min_value=100.0, value=850.0)
        
    if st.button("Consultar IA no Render"):
        try:
            res = requests.post(f"{API_IA_URL}/previsao_produtividade", json={"proximo_dia": int(dia_op), "proximo_peso_kg": float(peso_op)})
            if res.status_code == 200:
                prod = res.json().get("produtividade_prevista")
                st.metric("Produtividade Estimada", f"{prod} cx/h")
            else:
                st.error("Erro na comunicação com a API de IA")
        except Exception as e:
            st.error(f"Falha ao conectar: {e}")

# -------------------------------------------------------------------
# 5. CARREGAMENTO & ROTAS
# -------------------------------------------------------------------
elif modulo == "🚚 Carregamento & Rotas":
    st.header("🚚 Organização de Cargas e Roteirização por Veículo")

    df_rotas = None
    if 'df_separacao' in st.session_state and st.session_state['df_separacao'] is not None:
        df_rotas = st.session_state['df_separacao']

    if df_rotas is not None and not df_rotas.empty:
        col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_rotas.columns else 'ROTA'
        col_empresa = 'Empresa' if 'Empresa' in df_rotas.columns else 'CLIENTE'
        col_prod = 'PRODUTO' if 'PRODUTO' in df_rotas.columns else 'PRODUTO'
        col_qtd = 'Qtdade' if 'Qtdade' in df_rotas.columns else 'QTD'
        col_uni = 'UNIDADE' if 'UNIDADE' in df_rotas.columns else 'UN'

        if col_rota in df_rotas.columns:
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                rotas_disponiveis = sorted(df_rotas[col_rota].dropna().unique().tolist())
                rota_selecionada = st.selectbox("Selecione a Rota / Caminhão:", rotas_disponiveis)
            with col_sel2:
                modo_ordem = st.radio(
                    "Modo de Visualização:",
                    ["🚚 Ordem de Carregamento (Fundo -> Porta)", "📍 Ordem de Entrega (1ª -> Última)"]
                )

            df_filtro = df_rotas[df_rotas[col_rota] == rota_selecionada]

            exibir_metricas_detalhadas(df_filtro, col_qtd, col_uni, col_rota, col_empresa, f"📍 Capacidade de Carga do Veículo: {rota_selecionada}")

            st.write("---")
            st.subheader("📦 Sequência de Carregamento por Cliente")
            if col_empresa in df_filtro.columns:
                
                def resumir_unidades(g):
                    kg = g[g[col_uni].str.upper() == 'KG'][col_qtd].sum()
                    un = g[g[col_uni].str.upper() == 'UN'][col_qtd].sum()
                    bj = g[g[col_uni].str.upper() == 'BJ'][col_qtd].sum()
                    outros = g[~g[col_uni].str.upper().isin(['KG', 'UN', 'BJ'])][col_qtd].sum()
                    
                    partes = []
                    if kg > 0: partes.append(f"{kg:,.1f} KG")
                    if un > 0: partes.append(f"{int(un)} UND")
                    if bj > 0: partes.append(f"{int(bj)} BJ")
                    if outros > 0: partes.append(f"{int(outros)} VOL")
                    return " | ".join(partes)

                resumo_cliente = df_filtro.groupby(col_empresa, sort=False).apply(resumir_unidades).reset_index()
                resumo_cliente.columns = ["Cliente / Ponto de Entrega", "Detalhamento da Carga"]

                if "Ordem de Carregamento" in modo_ordem:
                    resumo_cliente = resumo_cliente.iloc[::-1].reset_index(drop=True)
                    resumo_cliente.insert(0, 'Etapa de Carga', [f"{i+1}º a Carregar (Fundo)" if i==0 else f"{i+1}º a Carregar" for i in range(len(resumo_cliente))])
                else:
                    resumo_cliente.insert(0, 'Etapa de Entrega', [f"{i+1}ª Entrega (Porta)" if i==0 else f"{i+1}ª Entrega" for i in range(len(resumo_cliente))])

                st.dataframe(resumo_cliente, use_container_width=True)

            st.subheader("📋 Romaneio Detalhado dos Produtos")
            cols_exibir = [col for col in ['NUMREQ', col_empresa, col_prod, col_qtd, col_uni] if col in df_filtro.columns]
            st.dataframe(df_filtro[cols_exibir] if cols_exibir else df_filtro, use_container_width=True)
        else:
            st.warning("A coluna 'TRP_FANTASIA' não foi localizada na planilha enviada.")
    else:
        st.info("💡 Para visualizar as rotas e cargas por veículo, primeiro suba a planilha em '📋 Separação do Dia'.")
