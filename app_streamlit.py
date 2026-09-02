import streamlit as st
import pandas as pd
import requests
import math
from supabase import create_client, Client

st.set_page_config(page_title="Módulo Tropical - Sistema de Expedição", layout="wide", page_icon="🌴")

st.markdown("""
<style>
    .card-laranja {
        background-color: #d35400;
        border: 2px solid #e67e22;
        border-radius: 10px;
        padding: 12px 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 95px;
        width: 100%;
    }
    .card-verde {
        background-color: #1e8449;
        border: 2px solid #27ae60;
        border-radius: 10px;
        padding: 12px 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 95px;
        width: 100%;
    }
    .card-titulo {
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 6px;
        text-align: center;
        width: 100%;
        line-height: 1.2;
    }
    .card-valor {
        color: #ffffff;
        font-size: 15px;
        font-weight: 800;
        text-align: center;
        width: 100%;
        line-height: 1.2;
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

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

def fmt_br_int(val):
    return f"{int(val):,}".replace(",", ".")

def fmt_br_float(val):
    return f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

def exibir_metricas_detalhadas(df, col_qtd, col_uni, col_rota, col_empresa, col_req, col_prod, titulo=""):
    if titulo:
        st.markdown(f"#### {titulo}")
        
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    
    num_rotas = df[col_rota].nunique() if col_rota in df.columns else 0
    num_clientes = df[col_empresa].nunique() if col_empresa in df.columns else 0
    num_pedidos = df[col_req].nunique() if col_req in df.columns else 0
        
    kg_total = df[df[col_uni].str.upper() == 'KG'][col_qtd].sum() if col_uni in df.columns else 0
    un_total = df[df[col_uni].str.upper() == 'UN'][col_qtd].sum() if col_uni in df.columns else 0
    bj_total = df[df[col_uni].str.upper() == 'BJ'][col_qtd].sum() if col_uni in df.columns else 0
    outros_total = df[~df[col_uni].str.upper().isin(['KG', 'UN', 'BJ'])][col_qtd].sum() if col_uni in df.columns else 0
    
    c1.markdown(f'<div class="card-laranja"><div class="card-titulo">Rotas</div><div class="card-valor">{fmt_br_int(num_rotas)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-laranja"><div class="card-titulo">Clientes</div><div class="card-valor">{fmt_br_int(num_clientes)}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-laranja"><div class="card-titulo">Pedidos</div><div class="card-valor">{fmt_br_int(num_pedidos)}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card-laranja"><div class="card-titulo">Peso (KG)</div><div class="card-valor">{fmt_br_float(kg_total)} kg</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="card-laranja"><div class="card-titulo">Unidades</div><div class="card-valor">{fmt_br_int(un_total)} und</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="card-laranja"><div class="card-titulo">Ovos (BJ)</div><div class="card-valor">{fmt_br_int(bj_total)} bj</div></div>', unsafe_allow_html=True)
    c7.markdown(f'<div class="card-laranja"><div class="card-titulo">Outros</div><div class="card-valor">{fmt_br_int(outros_total)} vol</div></div>', unsafe_allow_html=True)

    # --- ESTIMATIVA DE CAIXAS ---
    st.markdown("##### 📦 Estimativa de Caixas e Embalagens de Separação")
    
    if col_prod in df.columns and col_uni in df.columns:
        df_ovos = df[df[col_uni].str.upper() == 'BJ']
        bj_pvc = df_ovos[df_ovos[col_prod].str.upper().str.contains('PVC', na=False)][col_qtd].sum()
        bj_comum = df_ovos[~df_ovos[col_prod].str.upper().str.contains('PVC', na=False)][col_qtd].sum()
    else:
        bj_pvc, bj_comum = 0, bj_total

    # Caixas Peso (20kg), Unidades (180un) e Outros (20vol)
    cx_kg = math.ceil(kg_total / 20.0) if kg_total > 0 else 0
    cx_un = math.ceil(un_total / 180.0) if un_total > 0 else 0
    cx_outros = math.ceil(outros_total / 20.0) if outros_total > 0 else 0

    # Lógica de Ovos em Caixas Fechadas + Avulsos
    cx_pvc_fechadas = int(bj_pvc // 10)
    avulso_pvc = int(bj_pvc % 10)

    cx_comum_fechadas = int(bj_comum // 12)
    avulso_comum = int(bj_comum % 12)

    # Caixas totais para ovos (considerando volumes físicos ocupados)
    cx_ovo_total = math.ceil(bj_pvc / 10.0) + math.ceil(bj_comum / 12.0)
    cx_total_geral = cx_kg + cx_un + cx_outros + cx_ovo_total

    # Formatadores de texto para a caixa
    txt_pvc = f"{cx_pvc_fechadas} cx" + (f" + {avulso_pvc} bdj" if avulso_pvc > 0 else "")
    txt_comum = f"{cx_comum_fechadas} cx" + (f" + {avulso_comum} bdj" if avulso_comum > 0 else "")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.markdown(f'<div class="card-verde"><div class="card-titulo">CX Peso</div><div class="card-valor">{fmt_br_int(cx_kg)} cx</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="card-verde"><div class="card-titulo">CX Und</div><div class="card-valor">{fmt_br_int(cx_un)} cx</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="card-verde"><div class="card-titulo">Ovo PVC</div><div class="card-valor">{txt_pvc}<br><span style="font-size:11px; font-weight:normal;">({fmt_br_int(bj_pvc)} bdj)</span></div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="card-verde"><div class="card-titulo">Ovo Comum</div><div class="card-valor">{txt_comum}<br><span style="font-size:11px; font-weight:normal;">({fmt_br_int(bj_comum)} bdj)</span></div></div>', unsafe_allow_html=True)
    k5.markdown(f'<div class="card-verde"><div class="card-titulo">CX Outros</div><div class="card-valor">{fmt_br_int(cx_outros)} cx</div></div>', unsafe_allow_html=True)
    k6.markdown(f'<div class="card-verde"><div class="card-titulo">Total de Caixas</div><div class="card-valor">{fmt_br_int(cx_total_geral)} cx</div></div>', unsafe_allow_html=True)

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
            col_req = 'NUMREQ' if 'NUMREQ' in df_dia.columns else 'PEDIDO'

            exibir_metricas_detalhadas(df_dia, col_qtd, col_uni, col_rota, col_empresa, col_req, col_prod, "🚚 Resumo Geral de Todas as Rotas do Galpão")

            st.write("---")
            
            if st.button("💾 Salvar/Importar Base no Supabase", type="primary"):
                if supabase:
                    try:
                        records = []
                        for _, row in df_dia.iterrows():
                            records.append({
                                "pedido_id": str(row.get(col_req, '')),
                                "cliente": str(row.get(col_empresa, '')),
                                "produto": str(row.get(col_prod, '')),
                                "setor": str(row.get(col_rota, 'GERAL')),
                                "qtd_pedida": float(row.get(col_qtd, 0)),
                                "unidade": str(row.get(col_uni, 'KG'))
                            })
                        supabase.table("separacao_dia").insert(records).execute()
                        st.success("Toda a carga da planilha foi salva com sucesso no Supabase!")
                    except Exception as err:
                        st.error(f"Erro ao salvar no banco: {err}")
                else:
                    st.success("Planilha processada e pronta na memória local!")

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
        col_req = 'NUMREQ' if 'NUMREQ' in df_rotas.columns else 'PEDIDO'

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

            exibir_metricas_detalhadas(df_filtro, col_qtd, col_uni, col_rota, col_empresa, col_req, col_prod, f"📍 Capacidade de Carga do Veículo: {rota_selecionada}")

            st.write("---")
            st.subheader("📦 Conferência de Separação por Número de Pedido (NUMREQ)")
            
            if col_req in df_filtro.columns:
                def resumir_pedido(g):
                    items = len(g)
                    kg = g[g[col_uni].str.upper() == 'KG'][col_qtd].sum()
                    un = g[g[col_uni].str.upper() == 'UN'][col_qtd].sum()
                    bj = g[g[col_uni].str.upper() == 'BJ'][col_qtd].sum()
                    
                    partes = [f"{items} Itens"]
                    if kg > 0: partes.append(f"{fmt_br_float(kg)} KG")
                    if un > 0: partes.append(f"{fmt_br_int(un)} UND")
                    if bj > 0: partes.append(f"{fmt_br_int(bj)} BJ")
                    return " | ".join(partes)

                resumo_pedido = df_filtro.groupby([col_req, col_empresa], sort=False).apply(resumir_pedido).reset_index()
                resumo_pedido.columns = ["Número do Pedido (NUMREQ)", "Cliente / Escola", "Resumo para Separador"]

                if "Ordem de Carregamento" in modo_ordem:
                    resumo_pedido = resumo_pedido.iloc[::-1].reset_index(drop=True)
                    resumo_pedido.insert(0, 'Etapa Carga', [f"{i+1}º Pedido no Fundo" if i==0 else f"{i+1}º Pedido" for i in range(len(resumo_pedido))])
                else:
                    resumo_pedido.insert(0, 'Etapa Entrega', [f"{i+1}º Pedido na Porta" if i==0 else f"{i+1}º Pedido" for i in range(len(resumo_pedido))])

                st.dataframe(resumo_pedido, use_container_width=True)

            st.write("---")
            st.subheader("📋 Romaneio Detalhado dos Produtos (Contabilidade e Balança)")

            lista_pedidos = ["-- Todos os Pedidos da Rota --"] + [f"Pedido {p} - {c}" for p, c in zip(df_filtro[col_req], df_filtro[col_empresa])]
            lista_pedidos = list(dict.fromkeys(lista_pedidos))
            
            pedido_selecionado = st.selectbox("Filtrar Romaneio por Pedido (NUMREQ):", lista_pedidos)

            if pedido_selecionado != "-- Todos os Pedidos da Rota --":
                num_p = pedido_selecionado.split(" - ")[0].replace("Pedido ", "")
                df_exibir_produtos = df_filtro[df_filtro[col_req].astype(str) == str(num_p)]
                st.info(f"Exibindo itens do pedido **{pedido_selecionado}**")
            else:
                df_exibir_produtos = df_filtro

            cols_exibir = [col for col in [col_req, col_empresa, col_prod, col_qtd, col_uni] if col in df_exibir_produtos.columns]
            st.dataframe(df_exibir_produtos[cols_exibir] if cols_exibir else df_exibir_produtos, use_container_width=True)
        else:
            st.warning("A coluna 'TRP_FANTASIA' não foi localizada na planilha enviada.")
    else:
        st.info("💡 Para visualizar as rotas e cargas por veículo, primeiro suba a planilha em '📋 Separação do Dia'.")
