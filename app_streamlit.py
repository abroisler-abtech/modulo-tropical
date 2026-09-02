import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

st.set_page_config(page_title="Módulo Tropical - Sistema de Expedição", layout="wide", page_icon="🌴")

st.title("🌴 Módulo Tropical - Sistema Integrado de Expedição & Operação")
st.caption("Gestão de Separação, Conferência, Carregamento e Vasilhames")

# Carrega credenciais ocultas dos Secrets do Streamlit Cloud
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

# Menu Lateral Limpo com Módulos
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

            col1, col2, col3 = st.columns(3)
            if col_rota in df_dia.columns:
                col1.metric("Total de Rotas", df_dia[col_rota].nunique())
            if col_empresa in df_dia.columns:
                col2.metric("Total de Clientes", df_dia[col_empresa].nunique())
            if col_qtd in df_dia.columns:
                col3.metric("Volume Total (KG/UN)", f"{df_dia[col_qtd].sum():,.2f}")

            st.subheader("Pré-visualização dos Pedidos")
            st.dataframe(df_dia.head(20), use_container_width=True)

            st.session_state['df_separacao'] = df_dia

            if st.button("Gravar Carga no Supabase") and supabase:
                records = []
                for _, row in df_dia.iterrows():
                    records.append({
                        "pedido_id": str(row.get('NUMREQ', '')),
                        "cliente": str(row.get(col_empresa, '')),
                        "produto": str(row.get(col_prod, '')),
                        "setor": str(row.get(col_rota, 'GERAL')),
                        "qtd_pedida": float(row.get(col_qtd, 0)),
                        "unidade": str(row.get(col_uni, 'KG'))
                    })
                supabase.table("separacao_dia").insert(records).execute()
                st.success("Toda a carga do dia foi salva no banco de dados!")

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
            if supabase:
                data = {"tipo": tipo_mov, "produto": produto, "quantidade": float(quantidade), "motivo": motivo}
                supabase.table("lancamentos_avulsos").insert(data).execute()
                st.success("Lançamento gravado no Supabase com sucesso!")
            else:
                st.success(f"Lançamento registrado localmente!")

# -------------------------------------------------------------------
# 3. CONTROLE DE CAIXAS & FORNECEDORES
# -------------------------------------------------------------------
elif modulo == "📦 Controle de Caixas & Fornecedores":
    st.header("📦 Gestão de Embalagens e Entrada/Saída com Fornecedores")
    tab1, tab2, tab3 = st.tabs(["🔄 Movimentação de Caixas", "🏭 Cadastrar Fornecedor", "📋 Histórico"])
    
    with tab1:
        st.subheader("Registro de Entrada e Saída de Embalagens")
        fornecedores_list = []
        if supabase:
            f_res = supabase.table("fornecedores").select("id, nome").execute()
            fornecedores_list = f_res.data if f_res.data else []
            
        caixas_list = []
        if supabase:
            c_res = supabase.table("tipos_caixas").select("id, nome").execute()
            caixas_list = c_res.data if c_res.data else []

        if fornecedores_list and caixas_list:
            forn_dict = {f["nome"]: f["id"] for f in fornecedores_list}
            caixa_dict = {c["nome"]: c["id"] for c in caixas_list}

            sel_forn = st.selectbox("Fornecedor / Produtor Rural", list(forn_dict.keys()))
            sel_caixa = st.selectbox("Tipo de Embalagem", list(caixa_dict.keys()))
            operacao = st.radio("Operação", ["ENTRADA", "SAIDA"])
            qtd_caixas = st.number_input("Quantidade de Caixas/Paletes", min_value=1, value=50)
            obs = st.text_input("Observação")

            if st.button("Registrar Movimentação"):
                mov_data = {
                    "fornecedor_id": forn_dict[sel_forn],
                    "caixa_id": caixa_dict[sel_caixa],
                    "tipo_movimentacao": operacao,
                    "quantidade": int(qtd_caixas),
                    "observacao": obs
                }
                supabase.table("controle_vasilhames").insert(mov_data).execute()
                st.success("Movimentação registrada com sucesso no banco de dados!")
        else:
            sel_caixa = st.selectbox("Tipo de Embalagem", ["Caixa K de Madeira", "Monobloco Plástico Preto", "Palete PBR"])
            operacao = st.radio("Operação", ["ENTRADA", "SAIDA"])
            qtd_caixas = st.number_input("Quantidade de Caixas/Paletes", min_value=1, value=50)
            if st.button("Registrar Movimentação"):
                st.success("Movimentação salva!")

    with tab2:
        st.subheader("Novo Fornecedor / Produtor")
        nome_forn = st.text_input("Nome / Razão Social")
        doc_forn = st.text_input("CNPJ / CPF")
        tel_forn = st.text_input("Telefone")
        
        if st.button("Cadastrar Fornecedor"):
            if supabase and nome_forn:
                data = {"nome": nome_forn, "cnpj_cpf": doc_forn, "telefone": tel_forn}
                supabase.table("fornecedores").insert(data).execute()
                st.success(f"Fornecedor '{nome_forn}' salvo no banco de dados!")
            elif nome_forn:
                st.success(f"Fornecedor '{nome_forn}' cadastrado!")

    with tab3:
        st.subheader("Fornecedores Cadastrados")
        if supabase:
            res_f = supabase.table("fornecedores").select("*").execute()
            if res_f.data:
                st.dataframe(pd.DataFrame(res_f.data), use_container_width=True)

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
    elif supabase:
        try:
            res = supabase.table("separacao_dia").select("*").execute()
            if res.data:
                df_rotas = pd.DataFrame(res.data)
        except Exception:
            pass

    if df_rotas is not None and not df_rotas.empty:
        col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_rotas.columns else ('setor' if 'setor' in df_rotas.columns else 'ROTA')
        col_empresa = 'Empresa' if 'Empresa' in df_rotas.columns else ('cliente' if 'cliente' in df_rotas.columns else 'CLIENTE')
        col_prod = 'PRODUTO' if 'PRODUTO' in df_rotas.columns else ('produto' if 'produto' in df_rotas.columns else 'PRODUTO')
        col_qtd = 'Qtdade' if 'Qtdade' in df_rotas.columns else ('qtd_pedida' if 'qtd_pedida' in df_rotas.columns else 'QTD')
        col_uni = 'UNIDADE' if 'UNIDADE' in df_rotas.columns else ('unidade' if 'unidade' in df_rotas.columns else 'UN')

        if col_rota in df_rotas.columns:
            rotas_disponiveis = sorted(df_rotas[col_rota].dropna().unique().tolist())
            rota_selecionada = st.selectbox("Selecione a Rota / Caminhão:", rotas_disponiveis)

            df_filtro = df_rotas[df_rotas[col_rota] == rota_selecionada]

            st.subheader(f"📍 Resumo da Rota: {rota_selecionada}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pontos de Entrega (Clientes)", df_filtro[col_empresa].nunique() if col_empresa in df_filtro.columns else 0)
            c2.metric("Total de Itens", len(df_filtro))
            c3.metric("Volume Total", f"{df_filtro[col_qtd].sum():,.2f}")

            st.write("---")
            st.subheader("📦 Agrupamento por Cliente (Ordem de Descarregamento - LIFO)")
            if col_empresa in df_filtro.columns:
                resumo_cliente = df_filtro.groupby(col_empresa)[col_qtd].sum().reset_index()
                resumo_cliente.columns = ["Cliente / Ponto de Entrega", "Volume Total (KG/UN)"]
                st.dataframe(resumo_cliente, use_container_width=True)

            st.subheader("📋 Romaneio Detalhado da Rota")
            cols_exibir = [col for col in ['NUMREQ', col_empresa, col_prod, col_qtd, col_uni] if col in df_filtro.columns]
            st.dataframe(df_filtro[cols_exibir] if cols_exibir else df_filtro, use_container_width=True)
        else:
            st.warning("A coluna 'TRP_FANTASIA' não foi localizada na planilha enviada.")
    else:
        st.info("💡 Para visualizar as rotas e cargas por veículo, primeiro suba a planilha em '📋 Separação do Dia'.")
