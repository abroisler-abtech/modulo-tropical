import streamlit as st
import pandas as pd

st.set_page_config(page_title="Módulo Tropical - Sistema de Expedição", layout="wide", page_icon="🌴")

st.title("🌴 Módulo Tropical - Sistema Integrado de Expedição & Operação")
st.caption("Gestão de Separação, Conferência, Carregamento e Vasilhames")

# Menu Navegação de Módulos
modulo = st.sidebar.radio(
    "Navegação do Módulo Tropical",
    [
        "📋 Separação do Dia",
        "✏️ Lançamentos Avulsos",
        "📦 Controle de Caixas & Fornecedores",
        "🔮 Previsão de IA",
        "🚚 Carregamento & Rotas"
    ]
)

if modulo == "📋 Separação do Dia":
    st.header("📋 Base de Separação Diária do Galpão")
    uploaded_file = st.file_uploader("Suba a planilha do dia (CSV ou Excel)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        df_dia = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("Pré-visualização da Carga:", df_dia.head())

elif modulo == "✏️ Lançamentos Avulsos":
    st.header("✏️ Lançamentos Avulsos e Ajustes de Estoque")
    with st.form("form_avulso"):
        tipo_mov = st.selectbox("Tipo", ["ENTRADA_AVULSA", "SAIDA_AVULSA", "PERDA", "SOBRA"])
        produto = st.text_input("Nome do Produto (Ex: Tomate Débora)")
        quantidade = st.number_input("Quantidade (KG/CX)", min_value=0.1, value=10.0)
        btn_salvar = st.form_submit_button("Salvar Lançamento")
        if btn_salvar:
            st.success(f"Lançamento de {tipo_mov} registrado para {produto}!")

elif modulo == "📦 Controle de Caixas & Fornecedores":
    st.header("📦 Gestão de Embalagens e Entrada/Saída com Fornecedores")
    tab1, tab2 = st.tabs(["🔄 Movimentação de Caixas", "🏭 Cadastrar Fornecedor"])
    
    with tab1:
        st.subheader("Registro de Entrada e Saída de Embalagens")
        fornecedor = st.text_input("Nome do Fornecedor / Produtor Rural")
        caixa = st.selectbox("Tipo de Embalagem", ["Caixa K de Madeira", "Monobloco Plástico Preto", "Palete PBR"])
        tipo = st.radio("Operação", ["ENTRADA", "SAIDA"])
        qtd = st.number_input("Quantidade de Caixas/Paletes", min_value=1, value=50)
        if st.button("Registrar Movimentação"):
            st.success(f"{tipo} de {qtd} caixas registrada para {fornecedor}!")

    with tab2:
        st.subheader("Novo Fornecedor")
        nome_forn = st.text_input("Nome / Produtor Rural")
        if st.button("Cadastrar Fornecedor"):
            st.success(f"Fornecedor {nome_forn} cadastrado com sucesso!")

elif modulo == "🔮 Previsão de IA":
    st.header("🔮 Previsão de Produtividade com IA")
    st.info("Este módulo se conectará à API do Render para projetar o tempo de separação.")

elif modulo == "🚚 Carregamento & Rotas":
    st.header("🚚 Organização de Cargas por Rota e Veículo")
    st.info("Módulo de montagem de rotas e expedição por veículo.")
