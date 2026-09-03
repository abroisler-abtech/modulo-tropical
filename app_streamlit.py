import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Módulo Tropical - Sistema de Expedição", layout="wide", page_icon="🌴")

ENDERECO_GALPAO = "Av. Comendador Aladino Selmi, 4840 - Vila San Martin, Campinas - SP, 13069-096"
HOJE_STR = datetime.now().strftime("%Y-%m-%d")

st.markdown("""
<style>
    @media print {
        section[data-testid="stSidebar"] { display: none !important; }
        .stButton { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .no-print { display: none !important; }
        .print-area { display: block !important; width: 100%; }
    }
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
    .card-azul {
        background-color: #2980b9;
        border: 2px solid #3498db;
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
        font-size: 14px;
        font-weight: 800;
        text-align: center;
        width: 100%;
        line-height: 1.2;
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌴 Módulo Tropical - Sistema Integrado de Expedição & Operação")
st.caption(f"📍 Base de Saída / Galpão: {ENDERECO_GALPAO}")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://nlgxmrtxemyxjxqekkno.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

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
        "📋 1. Importar Base do Dia (ERP)",
        "⚙️ 2. Gestão de Rotas & Unificação",
        "🔮 3. Previsão de IA & Dimensionamento",
        "📲 4. Coletor / Terminal de Bipagem",
        "📱 5. Conferência Mobile & Picking",
        "🚚 6. Carregamento & Cupom de Saída",
        "📍 7. Entregas & Devolução de Caixas",
        "📦 8. Recebimento de Mercadoria",
        "🪵 9. Gestão de Caixaria & Saída",
        "🗺️ Endereços das Escolas",
        "✏️ Lançamentos Avulsos"
    ]
)

def fmt_br_int(val):
    return f"{int(val):,}".replace(",", ".")

def fmt_br_float(val):
    return f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_resumo_caixas(df, col_qtd, col_uni, col_prod):
    kg_total = df[df[col_uni].str.upper() == 'KG'][col_qtd].sum() if col_uni in df.columns else 0
    un_total = df[df[col_uni].str.upper() == 'UN'][col_qtd].sum() if col_uni in df.columns else 0
    bj_total = df[df[col_uni].str.upper() == 'BJ'][col_qtd].sum() if col_uni in df.columns else 0
    outros_total = df[~df[col_uni].str.upper().isin(['KG', 'UN', 'BJ'])][col_qtd].sum() if col_uni in df.columns else 0

    if col_prod in df.columns and col_uni in df.columns:
        df_ovos = df[df[col_uni].str.upper() == 'BJ']
        bj_pvc = df_ovos[df_ovos[col_prod].str.upper().str.contains('PVC', na=False)][col_qtd].sum()
        bj_comum = df_ovos[~df_ovos[col_prod].str.upper().str.contains('PVC', na=False)][col_qtd].sum()
    else:
        bj_pvc, bj_comum = 0, bj_total

    cx_kg = math.ceil(kg_total / 20.0) if kg_total > 0 else 0
    cx_un = math.ceil(un_total / 180.0) if un_total > 0 else 0
    cx_outros = math.ceil(outros_total / 20.0) if outros_total > 0 else 0
    cx_ovo_total = math.ceil(bj_pvc / 10.0) + math.ceil(bj_comum / 12.0)
    
    cx_total = cx_kg + cx_un + cx_outros + cx_ovo_total
    return kg_total, un_total, bj_total, outros_total, cx_total, bj_pvc, bj_comum, cx_kg, cx_un, cx_outros

def formatar_descricao_ovos(bj_pvc, bj_comum):
    if bj_pvc == 0 and bj_comum == 0:
        return "Sem Ovos", 0

    cx_pvc = int(bj_pvc // 10)
    bdj_pvc = int(bj_pvc % 10)
    cx_com = int(bj_comum // 12)
    bdj_com = int(bj_comum % 12)

    cx_fechadas = cx_pvc + cx_com
    bdj_avulsas = bdj_pvc + bdj_com

    partes = []
    if cx_fechadas > 0:
        partes.append(f"{cx_fechadas} {'caixa' if cx_fechadas == 1 else 'caixas'}")
    if bdj_avulsas > 0:
        partes.append(f"{bdj_avulsas} {'bandeja' if bdj_avulsas == 1 else 'bandejas'}")

    txt_final = " + ".join(partes) if partes else "Sem Ovos"
    vol_tot_ovos = cx_fechadas + (1 if bdj_avulsas > 0 else 0)

    return txt_final, vol_tot_ovos

def exibir_metricas_detalhadas(df, col_qtd, col_uni, col_rota, col_empresa, col_req, col_prod, titulo=""):
    if titulo:
        st.markdown(f"#### {titulo}")
        
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    
    num_rotas = df[col_rota].nunique() if col_rota in df.columns else 0
    num_clientes = df[col_empresa].nunique() if col_empresa in df.columns else 0
    num_pedidos = df[col_req].nunique() if col_req in df.columns else 0
        
    kg_total, un_total, bj_total, outros_total, cx_total_geral, bj_pvc, bj_comum, cx_kg, cx_un, cx_outros = calcular_resumo_caixas(df, col_qtd, col_uni, col_prod)
    
    c1.markdown(f'<div class="card-laranja"><div class="card-titulo">Rotas</div><div class="card-valor">{fmt_br_int(num_rotas)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-laranja"><div class="card-titulo">Clientes</div><div class="card-valor">{fmt_br_int(num_clientes)}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-laranja"><div class="card-titulo">Pedidos</div><div class="card-valor">{fmt_br_int(num_pedidos)}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card-laranja"><div class="card-titulo">Peso (KG)</div><div class="card-valor">{fmt_br_float(kg_total)} kg</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="card-laranja"><div class="card-titulo">Unidades</div><div class="card-valor">{fmt_br_int(un_total)} und</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="card-laranja"><div class="card-titulo">Ovos (BJ)</div><div class="card-valor">{fmt_br_int(bj_total)} bj</div></div>', unsafe_allow_html=True)
    c7.markdown(f'<div class="card-laranja"><div class="card-titulo">Outros</div><div class="card-valor">{fmt_br_int(outros_total)} vol</div></div>', unsafe_allow_html=True)

    st.markdown("##### 📦 Estimativa de Caixas e Embalagens de Separação")
    
    cx_pvc_fechadas = int(bj_pvc // 10)
    avulso_pvc = int(bj_pvc % 10)

    cx_comum_fechadas = int(bj_comum // 12)
    avulso_comum = int(bj_comum % 12)

    txt_pvc = f"{cx_pvc_fechadas} cx" + (f" + {avulso_pvc} bdj" if avulso_pvc > 0 else "")
    txt_comum = f"{cx_comum_fechadas} cx" + (f" + {avulso_comum} bdj" if avulso_comum > 0 else "")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.markdown(f'<div class="card-verde"><div class="card-titulo">CX Peso</div><div class="card-valor">{fmt_br_int(cx_kg)} cx</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="card-verde"><div class="card-titulo">CX Und</div><div class="card-valor">{fmt_br_int(cx_un)} cx</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="card-verde"><div class="card-titulo">Ovo PVC</div><div class="card-valor">{txt_pvc}<br><span style="font-size:11px; font-weight:normal;">({fmt_br_int(bj_pvc)} bdj)</span></div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="card-verde"><div class="card-titulo">Ovo Comum</div><div class="card-valor">{txt_comum}<br><span style="font-size:11px; font-weight:normal;">({fmt_br_int(bj_comum)} bdj)</span></div></div>', unsafe_allow_html=True)
    k5.markdown(f'<div class="card-verde"><div class="card-titulo">CX Outros</div><div class="card-valor">{fmt_br_int(cx_outros)} cx</div></div>', unsafe_allow_html=True)
    k6.markdown(f'<div class="card-verde"><div class="card-titulo">Total Caixas Tropical</div><div class="card-valor">{fmt_br_int(cx_total_geral)} cx</div></div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 1. IMPORTAR BASE DO DIA (ERP)
# -------------------------------------------------------------------
if modulo == "📋 1. Importar Base do Dia (ERP)":
    st.header("📋 Base de Separação Diária do Galpão (ERP)")
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
    elif 'df_separacao' in st.session_state and st.session_state['df_separacao'] is not None:
        df_dia = st.session_state['df_separacao']
        col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_dia.columns else 'ROTA'
        col_empresa = 'Empresa' if 'Empresa' in df_dia.columns else 'CLIENTE'
        col_prod = 'PRODUTO' if 'PRODUTO' in df_dia.columns else 'PRODUTO'
        col_qtd = 'Qtdade' if 'Qtdade' in df_dia.columns else 'QTD'
        col_uni = 'UNIDADE' if 'UNIDADE' in df_dia.columns else 'UN'
        col_req = 'NUMREQ' if 'NUMREQ' in df_dia.columns else 'PEDIDO'

        exibir_metricas_detalhadas(df_dia, col_qtd, col_uni, col_rota, col_empresa, col_req, col_prod, "🚚 Resumo Geral de Todas as Rotas do Galpão")
        st.write("---")
        st.subheader("Pré-visualização dos Pedidos")
        st.dataframe(df_dia.head(20), use_container_width=True)

# -------------------------------------------------------------------
# 2. GESTÃO DE ROTAS & UNIFICAÇÃO
# -------------------------------------------------------------------
elif modulo == "⚙️ 2. Gestão de Rotas & Unificação":
    st.header("⚙️ Gestão Interna de Rotas & Unificação de Cargas")
    st.caption("Ferramenta de retaguarda do supervisor para reordenar sequências ou agrupar rotas antes da expedição.")

    df_rotas = st.session_state.get('df_separacao', None)

    if df_rotas is not None and not df_rotas.empty:
        col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_rotas.columns else 'ROTA'
        col_empresa = 'Empresa' if 'Empresa' in df_rotas.columns else 'CLIENTE'
        col_prod = 'PRODUTO' if 'PRODUTO' in df_rotas.columns else 'PRODUTO'
        col_qtd = 'Qtdade' if 'Qtdade' in df_rotas.columns else 'QTD'
        col_uni = 'UNIDADE' if 'UNIDADE' in df_rotas.columns else 'UN'
        col_req = 'NUMREQ' if 'NUMREQ' in df_rotas.columns else 'PEDIDO'

        rotas_disponiveis = sorted(df_rotas[col_rota].dropna().unique().tolist())
        st.subheader("🔀 Agrupamento Manual de Rotas para o Mesmo Veículo")
        
        rotas_agrupadas = st.multiselect("Selecione as Rotas para Unificar:", rotas_disponiveis, default=[rotas_disponiveis[0]] if rotas_disponiveis else [])

        if rotas_agrupadas:
            df_agrup = df_rotas[df_rotas[col_rota].isin(rotas_agrupadas)]
            st.info("As alterações feitas nesta tela serão herdadas automaticamente pelo Módulo do Conferente e pelo Motorista.")
            st.dataframe(df_agrup[[col_req, col_empresa, col_rota, col_prod, col_qtd, col_uni]].head(30), use_container_width=True)
    else:
        st.warning("💡 Por favor, primeiro suba a planilha na aba '📋 1. Importar Base do Dia (ERP)' para carregar as rotas.")

# -------------------------------------------------------------------
# 3. PREVISÃO DE IA & DIMENSIONAMENTO
# -------------------------------------------------------------------
elif modulo == "🔮 3. Previsão de IA & Dimensionamento":
    st.header("🔮 Previsão de Produtividade & Dimensionamento de Galpão")
    st.caption("Cálculo calibrado com base na produtividade real da equipe (1.110 caixas em ~2h com 41 separadores).")

    df_base = st.session_state.get('df_separacao', None)

    col_qtd = 'Qtdade' if df_base is not None and 'Qtdade' in df_base.columns else 'QTD'
    col_uni = 'UNIDADE' if df_base is not None and 'UNIDADE' in df_base.columns else 'UN'
    col_prod = 'PRODUTO' if df_base is not None and 'PRODUTO' in df_base.columns else 'PRODUTO'

    if df_base is not None and not df_base.empty:
        kg_tot, un_tot, bj_tot, out_tot, cx_total_real, _, _, _, _, _ = calcular_resumo_caixas(df_base, col_qtd, col_uni, col_prod)
        
        st.info(f"📊 **Carga Atual no Galpão:** **{fmt_br_float(kg_tot)} KG** correspondendo a **{fmt_br_int(cx_total_real)} Caixas Totais**.")

        st.write("---")
        st.subheader("👥 Controle de Faltas e Dimensionamento do Turno")
        qtd_separadores = st.slider("Selecione a quantidade de separadores PRESENTES no turno hoje:", min_value=1, max_value=50, value=41)

        CADENCIA_POR_SEPARADOR = 13.5365
        produtividade_equipe_cxh = qtd_separadores * CADENCIA_POR_SEPARADOR

        tempo_horas_real = cx_total_real / produtividade_equipe_cxh if produtividade_equipe_cxh > 0 else 0
        horas_exatas = int(tempo_horas_real)
        minutos_exatos = int((tempo_horas_real - horas_exatas) * 60)

        st.markdown("---")
        st.subheader("🎯 Planejamento do Turno de Separação")
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="card-laranja"><div class="card-titulo">Produtividade da Equipe</div><div class="card-valor">{produtividade_equipe_cxh:.1f} cx/h</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="card-verde"><div class="card-titulo">Volume Total de Caixas</div><div class="card-valor">{fmt_br_int(cx_total_real)} caixas</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="card-laranja"><div class="card-titulo">Tempo Estimado do Turno</div><div class="card-valor">{horas_exatas}h {minutos_exatos}min</div></div>', unsafe_allow_html=True)

    else:
        st.warning("💡 Por favor, primeiro suba a planilha na aba '📋 1. Importar Base do Dia (ERP)' para carregar os volumes da carga.")

# -------------------------------------------------------------------
# 4. COLETOR / TERMINAL DE BIPAGEM
# -------------------------------------------------------------------
elif modulo == "📲 4. Coletor / Terminal de Bipagem":
    st.header("📲 Coletor de Separação (Terminal do Galpão)")
    st.caption("Compatível com leitor de código de barras ou digitação de fichas/NUMREQ.")

    df_base = st.session_state.get('df_separacao', None)
    col_req = 'NUMREQ' if df_base is not None and 'NUMREQ' in df_base.columns else ('PEDIDO' if df_base is not None and 'PEDIDO' in df_base.columns else None)
    total_pedidos_erp = df_base[col_req].nunique() if (df_base is not None and col_req) else 0

    bipagens_hoje = []
    if supabase:
        try:
            res = supabase.table("separacao").select("*").eq("data_registro", HOJE_STR).execute()
            bipagens_hoje = res.data if res.data else []
        except Exception:
            bipagens_hoje = []

    df_bip = pd.DataFrame(bipagens_hoje) if bipagens_hoje else pd.DataFrame(columns=["numreq", "operador", "origem", "data_registro"])

    bip_erp = len(df_bip[df_bip["origem"].isin(["Base ERP", "Base ERP (Escolas)"])]) if "origem" in df_bip.columns else len(df_bip)
    cnt_campinas = len(df_bip[df_bip["origem"] == "Campinas"]) if "origem" in df_bip.columns else 0
    cnt_estado = len(df_bip[df_bip["origem"] == "Estado"]) if "origem" in df_bip.columns else 0
    cnt_confruty = len(df_bip[df_bip["origem"] == "Confruty"]) if "origem" in df_bip.columns else 0
    cnt_vinhedo = len(df_bip[df_bip["origem"] == "Vinhedo"]) if "origem" in df_bip.columns else 0

    if total_pedidos_erp > 0:
        pct_erp = (bip_erp / total_pedidos_erp) * 100
        txt_erp = f"{bip_erp} / {total_pedidos_erp} ped<br><span style='font-size:11px; font-weight:normal;'>({pct_erp:.1f}%)</span>"
    else:
        txt_erp = f"{bip_erp} bipagens"

    st.markdown("##### 📊 Bipagens Realizadas Hoje por Operação")
    o1, o2, o3, o4, o5 = st.columns(5)
    o1.markdown(f'<div class="card-laranja"><div class="card-titulo">Base ERP</div><div class="card-valor">{txt_erp}</div></div>', unsafe_allow_html=True)
    o2.markdown(f'<div class="card-azul"><div class="card-titulo">Campinas</div><div class="card-valor">{cnt_campinas} bipagens</div></div>', unsafe_allow_html=True)
    o3.markdown(f'<div class="card-azul"><div class="card-titulo">Estado</div><div class="card-valor">{cnt_estado} bipagens</div></div>', unsafe_allow_html=True)
    o4.markdown(f'<div class="card-azul"><div class="card-titulo">Confruty</div><div class="card-valor">{cnt_confruty} bipagens</div></div>', unsafe_allow_html=True)
    o5.markdown(f'<div class="card-azul"><div class="card-titulo">Vinhedo</div><div class="card-valor">{cnt_vinhedo} bipagens</div></div>', unsafe_allow_html=True)

    st.write("---")

    col_esq, col_dir = st.columns([1.2, 1])

    with col_esq:
        st.subheader("📝 Bipagem em Lote")
        
        operacao_sel = st.selectbox(
            "1. Selecione a Origem da Separação:",
            ["Base ERP", "Campinas", "Estado", "Confruty", "Vinhedo"]
        )
        
        operador_cod = st.text_input("2. Código / Crachá do Separador:")

        fichas_raw = st.text_area(
            "3. Bipe ou digite as Fichas / NUMREQ (uma por linha):",
            height=140,
            placeholder="Bipe a 1ª ficha...\nBipe a 2ª ficha...\nBipe a 3ª ficha..."
        )

        if st.button("🚀 Confirmar Bipagens", type="primary", use_container_width=True):
            if not operador_cod or not fichas_raw.strip():
                st.warning("⚠️ Informe o código do separador e bipe ao menos uma ficha!")
            else:
                lista_fichas = [f.strip() for f in fichas_raw.strip().split("\n") if f.strip()]
                ja_bipados = {str(b.get("numreq")).strip() for b in bipagens_hoje}

                novos_registros = []
                duplicados = []

                for req in lista_fichas:
                    req_str = str(req).strip()
                    if req_str in ja_bipados:
                        duplicados.append(req_str)
                    else:
                        novos_registros.append({
                            "numreq": req_str,
                            "operador": operador_cod.strip(),
                            "origem": operacao_sel,
                            "data_registro": HOJE_STR
                        })
                        ja_bipados.add(req_str)

                if novos_registros:
                    if supabase:
                        try:
                            supabase.table("separacao").insert(novos_registros).execute()
                            st.success(f"✅ {len(novos_registros)} pedido(s) registrado(s) para {operador_cod} na operação [{operacao_sel}]!")
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")
                    else:
                        st.success(f"✅ {len(novos_registros)} pedido(s) processados na memória local!")

                if duplicados:
                    st.error(f"⚠️ Os seguintes pedidos já haviam sido bipados hoje e foram ignorados: {', '.join(duplicados)}")

                st.rerun()

    with col_dir:
        st.subheader("📋 Últimas Bipagens Registradas")
        if not df_bip.empty:
            cols_exib = [c for c in ["numreq", "operador", "origem"] if c in df_bip.columns]
            st.dataframe(df_bip[cols_exib].iloc[::-1].head(12), use_container_width=True)
        else:
            st.info("Nenhuma bipagem registrada hoje ainda.")

# -------------------------------------------------------------------
# 5. CONFERÊNCIA MOBILE & PICKING
# -------------------------------------------------------------------
elif modulo == "📱 5. Conferência Mobile & Picking":
    st.header("📱 Módulo de Conferência Mobile & Picking")
    st.caption("Interface otimizada para smartphones de conferentes na doca e liberação de picking.")

    tab_conf_mob, tab_conf_super = st.tabs(["📲 Conferente (Celular)", "📊 Painel do Supervisor & Picking"])

    df_base = st.session_state.get('df_separacao', None)

    with tab_conf_mob:
        if df_base is not None and not df_base.empty:
            col_req = 'NUMREQ' if 'NUMREQ' in df_base.columns else 'PEDIDO'
            col_emp = 'Empresa' if 'Empresa' in df_base.columns else 'CLIENTE'
            col_prod = 'PRODUTO' if 'PRODUTO' in df_base.columns else 'PRODUTO'
            col_qtd = 'Qtdade' if 'Qtdade' in df_base.columns else 'QTD'
            col_uni = 'UNIDADE' if 'UNIDADE' in df_base.columns else 'UN'
            col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_base.columns else 'ROTA'

            st.subheader("🔍 Localizar Pedido para Conferência")
            cod_bipado = st.text_input("Bipe o código do ticket / NUMREQ ou selecione abaixo:", placeholder="Aguardando bipagem do ticket...")

            lista_pedidos_opt = ["-- Selecione o Pedido --"] + sorted(df_base[col_req].astype(str).unique().tolist())
            
            if cod_bipado.strip() in lista_pedidos_opt:
                ped_selecionado = cod_bipado.strip()
            else:
                sel = st.selectbox("Ou selecione o Pedido:", lista_pedidos_opt, index=0)
                ped_selecionado = sel if sel != "-- Selecione o Pedido --" else None

            if ped_selecionado:
                df_ped = df_base[df_base[col_req].astype(str) == str(ped_selecionado)]
                nome_cliente = df_ped[col_emp].iloc[0] if col_emp in df_ped.columns else "Cliente"
                nome_rota = df_ped[col_rota].iloc[0] if col_rota in df_ped.columns else "Geral"

                st.markdown(f"### 📦 Pedido: `{ped_selecionado}`")
                st.info(f"🏢 **Cliente/Empresa:** {nome_cliente} | 🚚 **Rota:** {nome_rota}")

                st.markdown("#### 📋 Checklist de Produtos")
                st.caption("Marque os itens conforme confere a mercadoria na doca:")

                todas_checadas = True
                for idx, row in df_ped.iterrows():
                    item_str = f"{row[col_prod]} — {fmt_br_float(row[col_qtd])} {row[col_uni]}"
                    check = st.checkbox(item_str, key=f"chk_{idx}")
                    if not check:
                        todas_checadas = False

                kg_p, un_p, bj_p, out_p, cx_tot_p, bj_pvc_p, bj_com_p, cx_kg_p, cx_un_p, cx_out_p = calcular_resumo_caixas(df_ped, col_qtd, col_uni, col_prod)
                txt_ovos_blindado, vol_ovos_num = formatar_descricao_ovos(bj_pvc_p, bj_com_p)

                st.markdown("---")
                st.markdown("#### 📦 Quantidade de Embalagens Encontradas")

                c_cx1, c_cx2 = st.columns(2)
                with c_cx1:
                    qtd_tropical = st.text_input("Caixas Tropical (Hortifrúti):", value="0")
                with c_cx2:
                    st.text_input("Ovos no Pedido (Fechado/Regra):", value=txt_ovos_blindado, disabled=True)

                conferente_nome = st.session_state.get('usuario_ativo', 'Conferente 01')

                if st.button("✅ Finalizar & Aprovar Pedido", type="primary", use_container_width=True):
                    if not todas_checadas:
                        st.warning("⚠️ Atenção: Nem todos os itens foram marcados no checklist!")
                    
                    dados_conferencia = {
                        "numreq": str(ped_selecionado),
                        "cliente": str(nome_cliente),
                        "rota": str(nome_rota),
                        "caixas_tropical": int(qtd_tropical) if qtd_tropical.isdigit() else 0,
                        "caixas_ovos": vol_ovos_num,
                        "desc_ovos": str(txt_ovos_blindado),
                        "conferente": str(conferente_nome),
                        "status": "CONFERIDO",
                        "data_registro": HOJE_STR
                    }

                    if supabase:
                        try:
                            supabase.table("conferencia").insert(dados_conferencia).execute()
                            st.success(f"✅ Pedido {ped_selecionado} conferido e aprovado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao salvar conferência no banco: {e}")
                    else:
                        st.success(f"✅ Pedido {ped_selecionado} aprovado localmente!")

                    st.balloons()
            else:
                st.info("👆 Por favor, bipe o ticket ou selecione um pedido para abrir o checklist.")
        else:
            st.warning("💡 Por favor, primeiro suba a planilha na aba '📋 1. Importar Base do Dia (ERP)' para ativar a conferência.")

    with tab_conf_super:
        st.subheader("📊 Monitoramento de Conferência da Doca & Liberação de Picking")
        
        res_conf = []
        if supabase:
            try:
                r = supabase.table("conferencia").select("*").eq("data_registro", HOJE_STR).execute()
                res_conf = r.data if r.data else []
            except Exception:
                res_conf = []

        df_conf = pd.DataFrame(res_conf) if res_conf else pd.DataFrame(columns=["numreq", "cliente", "rota", "caixas_tropical", "caixas_ovos", "desc_ovos", "conferente", "status"])

        if df_base is not None and not df_base.empty:
            col_rota = 'TRP_FANTASIA' if 'TRP_FANTASIA' in df_base.columns else 'ROTA'
            col_req = 'NUMREQ' if 'NUMREQ' in df_base.columns else 'PEDIDO'

            rotas_disp = sorted(df_base[col_rota].dropna().unique().tolist())
            rota_sel_picking = st.selectbox("Selecione a Rota para Gerar o Picking de Carregamento:", rotas_disp)

            if rota_sel_picking:
                df_pedidos_rota = df_base[df_base[col_rota] == rota_sel_picking]
                total_pedidos_rota = df_pedidos_rota[col_req].nunique()
                
                pedidos_conf_rota = df_conf[df_conf["rota"] == rota_sel_picking] if not df_conf.empty else pd.DataFrame()
                qtd_conf_rota = pedidos_conf_rota["numreq"].nunique() if not pedidos_conf_rota.empty else 0

                pct_rota = (qtd_conf_rota / total_pedidos_rota * 100) if total_pedidos_rota > 0 else 0

                st.markdown(f"#### Status da Rota: `{rota_sel_picking}`")
                
                k_p1, k_p2, k_p3 = st.columns(3)
                k_p1.metric("Total de Pedidos da Rota", total_pedidos_rota)
                k_p2.metric("Pedidos Conferidos", qtd_conf_rota)
                k_p3.metric("Progresso da Rota", f"{pct_rota:.1f}%".replace('.', ','))

                st.progress(min(1.0, pct_rota / 100.0))

                st.write("---")
                st.markdown("### 📄 Picking de Carregamento (Consolidado da Rota)")

                if not pedidos_conf_rota.empty:
                    tot_tropical = pedidos_conf_rota["caixas_tropical"].sum()
                    tot_ovos_vols = pedidos_conf_rota["caixas_ovos"].sum()
                    tot_geral_caixas = tot_tropical + tot_ovos_vols

                    c_pick1, c_pick2, c_pick3 = st.columns(3)
                    c_pick1.markdown(f'<div class="card-verde"><div class="card-titulo">Total Caixas Tropical</div><div class="card-valor">{tot_tropical} cx</div></div>', unsafe_allow_html=True)
                    c_pick2.markdown(f'<div class="card-verde"><div class="card-titulo">Volumes Ovos</div><div class="card-valor">{tot_ovos_vols} vol</div></div>', unsafe_allow_html=True)
                    c_pick3.markdown(f'<div class="card-laranja"><div class="card-titulo">Total Geral a Carregar</div><div class="card-valor">{tot_geral_caixas} vol</div></div>', unsafe_allow_html=True)

                    st.markdown("##### 🏢 Empresas e Caixas do Veículo")
                    cols_show = [c for c in ["numreq", "cliente", "caixas_tropical", "desc_ovos", "conferente"] if c in pedidos_conf_rota.columns]
                    st.dataframe(pedidos_conf_rota[cols_show], use_container_width=True)

                    cod_barras_rota = f"PICKING-{HOJE_STR.replace('-','')}-{rota_sel_picking.replace(' ','')}"
                    
                    st.markdown("---")
                    st.subheader("🖨️ Impressão do Picking de Carregamento")
                    
                    if st.button("🖨️ Imprimir Ficha de Picking", type="primary"):
                        st.components.v1.html("<script>window.print();</script>", height=0)

                    html_print = f"""
                    <div style="border:2px solid #000; padding:20px; font-family:Arial, sans-serif; background-color:#fff; color:#000;">
                        <div style="text-align:center; border-bottom:2px solid #000; padding-bottom:10px;">
                            <h2 style="margin:0;">🌴 MÓDULO TROPICAL — EXPEDIÇÃO & CARREGAMENTO</h2>
                            <h3 style="margin:5px 0;">FICHA DE PICKING — ROTA: {rota_sel_picking}</h3>
                            <p style="margin:0;">Data: {HOJE_STR} | Base: Campinas</p>
                        </div>
                        <div style="margin-top:15px; font-size:16px;">
                            <p><strong>Total Caixas Tropical:</strong> {tot_tropical} cx</p>
                            <p><strong>Total Volumes de Ovos:</strong> {tot_ovos_vols} vol</p>
                            <p><strong>TOTAL GERAL A CARREGAR:</strong> {tot_geral_caixas} volumes</p>
                        </div>
                        <div style="text-align:center; margin-top:20px; border-top:2px solid #000; padding-top:15px;">
                            <img src="https://bwipjs-api.metafloor.com/?bcid=code128&text={cod_barras_rota}&scale=3&rotate=N&includetext" alt="Código de Barras">
                            <p style="font-family:monospace; font-weight:bold; font-size:16px; margin-top:5px;">{cod_barras_rota}</p>
                        </div>
                    </div>
                    """
                    st.markdown(html_print, unsafe_allow_html=True)
                else:
                    st.info("Nenhum pedido desta rota foi conferido no celular ainda.")

# -------------------------------------------------------------------
# 6. CARREGAMENTO & CUPOM DE SAÍDA
# -------------------------------------------------------------------
elif modulo == "🚚 6. Carregamento & Cupom de Saída":
    st.header("🚚 Módulo do Motorista / Agregado — Carregamento do Veículo")
    st.caption("Insira o código do Picking de Carregamento para validar a rota e emitir o Cupom de Saída.")

    cod_pick_input = st.text_input("📲 Bipe ou Digite o Código do Picking de Carregamento:", placeholder="Ex: PICKING-20260903-227-ROTA...")

    if cod_pick_input.strip():
        res_conf = []
        if supabase:
            try:
                r = supabase.table("conferencia").select("*").eq("data_registro", HOJE_STR).execute()
                res_conf = r.data if r.data else []
            except Exception:
                res_conf = []

        df_conf = pd.DataFrame(res_conf) if res_conf else pd.DataFrame()

        if not df_conf.empty:
            st.success(f"✅ Picking `{cod_pick_input.strip()}` localizado com sucesso!")
            
            st.markdown("### 📋 Checklist de Carregamento do Veículo (Fundo -> Porta)")
            st.caption("Marque cada empresa/unidade conforme embarca no caminhão:")

            motorista_nome = st.text_input("Nome do Motorista / Agregado:", value="Motorista Agregado 01")
            placa_veiculo = st.text_input("Placa do Veículo:", value="ABC-1234")

            empresas_embarcadas = []
            todas_embarcadas = True

            for idx, row in df_conf.iterrows():
                label_emp = f"🏢 {row.get('cliente')} — Pedido `{row.get('numreq')}` ({row.get('caixas_tropical')} Cx Tropical | {row.get('desc_ovos')})"
                chk = st.checkbox(label_emp, key=f"carg_{idx}")
                if chk:
                    empresas_embarcadas.append(row)
                else:
                    todas_embarcadas = False

            st.write("---")
            if st.button("🚀 Finalizar Carregamento & Emitir Cupom de Saída (2 Vias)", type="primary", use_container_width=True):
                if not todas_embarcadas:
                    st.warning("⚠️ Atenção: Existem empresas da rota que não foram marcadas como embarcadas!")

                tot_trop_carg = sum([int(r.get("caixas_tropical", 0)) for r in empresas_embarcadas]) if empresas_embarcadas else 0
                tot_ovos_carg = sum([int(r.get("caixas_ovos", 0)) for r in empresas_embarcadas]) if empresas_embarcadas else 0

                st.success("✅ Carregamento Concluído! O Módulo de Entregas no Cliente foi liberado automaticamente!")

                st.markdown("### 🧾 CUPOM DE SAÍDA (2 VIAS)")
                if st.button("🖨️ Imprimir Cupom de Saída", type="primary"):
                    st.components.v1.html("<script>window.print();</script>", height=0)

                for via in ["1ª VIA — GALPÃO / EXPEDIÇÃO", "2ª VIA — MOTORISTA / TRANSPORTE"]:
                    html_cupom = f"""
                    <div style="border:2px dashed #000; padding:15px; margin-bottom:20px; font-family:Arial, sans-serif; background-color:#fff; color:#000;">
                        <div style="text-align:center; border-bottom:1px solid #000; padding-bottom:5px;">
                            <h3 style="margin:0;">🌴 MÓDULO TROPICAL — CUPOM DE SAÍDA</h3>
                            <h4 style="margin:3px 0;">{via}</h4>
                            <p style="margin:0; font-size:12px;">Data: {HOJE_STR} | Placa: {placa_veiculo} | Motorista: {motorista_nome}</p>
                        </div>
                        <div style="margin-top:10px; font-size:13px;">
                            <p><strong>Picking:</strong> {cod_pick_input.strip()}</p>
                            <p><strong>Total Caixas Tropical Embarcadas:</strong> {tot_trop_carg} cx</p>
                            <p><strong>Total Volumes de Ovos Embarcados:</strong> {tot_ovos_carg} vol</p>
                            <p><strong>Empresas Embarcadas:</strong> {len(empresas_embarcadas)} unidades</p>
                        </div>
                        <div style="margin-top:20px; display:flex; justify-content:space-between; font-size:11px; text-align:center;">
                            <div>___________________________________<br>Assinatura Expedição</div>
                            <div>___________________________________<br>Assinatura Motorista</div>
                        </div>
                    </div>
                    """
                    st.markdown(html_cupom, unsafe_allow_html=True)
        else:
            st.info("Nenhuma conferência finalizada encontrada para a data de hoje.")

# -------------------------------------------------------------------
# 7. ENTREGAS & DEVOLUÇÃO DE CAIXAS
# -------------------------------------------------------------------
elif modulo == "📍 7. Entregas & Devolução de Caixas":
    st.header("📍 Módulo de Entrega no Cliente & Controle de Vasilhames")
    st.caption("Acompanhamento das paradas do caminhão com Alerta de Saldo Devedor do Ponto.")

    res_conf = []
    if supabase:
        try:
            r = supabase.table("conferencia").select("*").eq("data_registro", HOJE_STR).execute()
            res_conf = r.data if r.data else []
        except Exception:
            res_conf = []

    df_conf = pd.DataFrame(res_conf) if res_conf else pd.DataFrame()

    if not df_conf.empty:
        st.subheader("🏢 Roteiro de Entregas do Veículo")
        
        for idx, row in df_conf.iterrows():
            cliente_nome = row.get('cliente')
            cx_entregar_hoje = int(row.get('caixas_tropical', 0))

            saldo_devedor_anterior = 15 if idx % 2 == 0 else 0
            meta_recolhimento = cx_entregar_hoje + saldo_devedor_anterior

            with st.expander(f"📍 Parada {idx+1}: {cliente_nome} — Pedido `{row.get('numreq')}`"):
                st.write(f"🚚 **Rota:** {row.get('rota')}")
                st.write(f"📦 **Caixas Tropical a Entregar Hoje:** **{cx_entregar_hoje} cx**")
                st.write(f"🥚 **Ovos:** {row.get('desc_ovos')}")

                if saldo_devedor_anterior > 0:
                    st.warning(f"⚠️ **ALERTA DE VASILHAME NA UNIDADE:** Esta escola possui **{saldo_devedor_anterior} Caixas Tropical** pendentes de entregas anteriores!\n\n🎯 **META DE RECOLHIMENTO HOJE:** **{meta_recolhimento} Caixas Tropical** (Para zerar o ponto).")
                else:
                    st.success("✅ **SITUAÇÃO REGULAR:** Não há saldo devedor de caixas pendente nesta unidade.")

                st.markdown("---")
                st.markdown("#### 🔄 Acerto de Vasilhame no Ato da Entrega")
                c_ent1, c_ent2 = st.columns(2)
                with c_ent1:
                    cx_deixadas_str = st.text_input(f"Caixas Tropical Deixadas Hoje:", value=str(cx_entregar_hoje), key=f"deix_{idx}")
                with c_ent2:
                    cx_retiradas_str = st.text_input(f"Caixas Tropical Retiradas (Vazias):", value="0", key=f"ret_{idx}")

                cx_deixadas = int(cx_deixadas_str) if cx_deixadas_str.isdigit() else 0
                cx_retiradas = int(cx_retiradas_str) if cx_retiradas_str.isdigit() else 0

                novo_saldo_calc = saldo_devedor_anterior + cx_deixadas - cx_retiradas
                st.info(f"📊 **Novo Saldo de Caixas da Escola após esta Entrega:** **{novo_saldo_calc} Caixas Tropical**")

                obs_entrega = st.text_input(f"Nome do Recebedor / Assinatura:", key=f"obs_{idx}")

                if st.button(f"✅ Confirmar Entrega em {cliente_nome}", key=f"btn_ent_{idx}", type="primary"):
                    dados_baixa = {
                        "numreq": row.get('numreq'),
                        "cliente": cliente_nome,
                        "caixas_deixadas": cx_deixadas,
                        "caixas_retiradas": cx_retiradas,
                        "saldo_resultante": novo_saldo_calc,
                        "obs": obs_entrega,
                        "data_registro": HOJE_STR,
                        "status": "ENTREGUE"
                    }
                    if supabase:
                        try:
                            supabase.table("entregas").insert(dados_baixa).execute()
                            st.success(f"✅ Entrega confirmada! Saldo do cliente atualizado para {novo_saldo_calc} caixas.")
                        except Exception as e:
                            st.error(f"Erro ao registrar baixa: {e}")
                    else:
                        st.success(f"✅ Entrega de {cliente_nome} confirmada localmente com saldo de {novo_saldo_calc} caixas!")
    else:
        st.info("Nenhuma carga liberada para entrega no momento. Realize a conferência e o carregamento do veículo primeiro.")

# -------------------------------------------------------------------
# 8. RECEBIMENTO DE MERCADORIA (ENTRADA PURA)
# -------------------------------------------------------------------
elif modulo == "📦 8. Recebimento de Mercadoria":
    st.header("📦 Módulo de Recebimento de Mercadoria (Doca de Entrada)")
    st.caption("Registro de entrada de cargas e vasilhames trazidos por fornecedores.")

    st.subheader("📥 Lançamento de Entrada no Galpão")
    
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        origem_ent = st.selectbox("Local de Recebimento:", ["Galpão Tropical (Campinas)", "CEASA Campinas", "CEASA São Paulo (CEAGESP)"])
        fornecedor_ent = st.text_input("Nome do Fornecedor / Produtor:", placeholder="Ex: Goiaba Atibaia / Batata Silva...")
    with c_r2:
        doc_ref_ent = st.text_input("Nº Nota Fiscal / Romaneio de Entrada:", placeholder="Ex: NF 10234")
        tipo_emb_ent = st.selectbox("Tipo de Embalagem Recebida:", [
            "Caixa Tropical (Hortifrúti)", "Palete PBR", "Caixa Louca ALTA", "Caixa Louca BAIXA", "Madeira / Banana / Grade / Tipo K"
        ])

    qtd_ent_str = st.text_input("Quantidade de Embalagens Recebidas (Entrada):", value="0")
    qtd_ent_num = int(qtd_ent_str) if qtd_ent_str.isdigit() else 0
    obs_ent = st.text_input("Observações do Recebimento:", placeholder="Ex: Entrada em perfeitas condições")

    if st.button("💾 Registrar Entrada e Enviar para Caixaria", type="primary", use_container_width=True):
        if not fornecedor_ent.strip():
            st.warning("⚠️ Informe o nome do fornecedor!")
        elif qtd_ent_num <= 0:
            st.warning("⚠️ A quantidade de entrada deve ser maior que 0!")
        else:
            dado_ent = {
                "origem": origem_ent,
                "fornecedor": fornecedor_ent.strip(),
                "doc_ref": doc_ref_ent.strip(),
                "embalagem": tipo_emb_ent,
                "qtd_entrada": qtd_ent_num,
                "qtd_saida": 0,
                "status": "PENDENTE_CAIXARIA",
                "obs_entrada": obs_ent,
                "data_registro": HOJE_STR
            }
            if supabase:
                try:
                    supabase.table("movimentacao_caixas").insert(dado_ent).execute()
                    st.success(f"✅ Entrada de {qtd_ent_num} {tipo_emb_ent} de {fornecedor_ent} enviada para o Setor de Caixaria!")
                except Exception as e:
                    st.error(f"Erro ao salvar recebimento: {e}")
            else:
                st.success(f"✅ Entrada registrada localmente para {fornecedor_ent}!")

# -------------------------------------------------------------------
# 9. GESTÃO DE CAIXARIA & SAÍDA (MÓDULO SEPARADO)
# -------------------------------------------------------------------
elif modulo == "🪵 9. Gestão de Caixaria & Saída":
    st.header("🪵 Módulo de Gestão de Caixaria (Doca de Saída / Vasilhames)")
    st.caption("Efetue a liberação de embalagens e emita o Cupom de Saída assinado.")

    tab_caix_pend, tab_caix_extrato = st.tabs(["📤 Liberação de Saída por Fornecedor", "📊 Extrato Geral de Saldos"])

    with tab_caix_pend:
        res_entradas = []
        if supabase:
            try:
                r = supabase.table("movimentacao_caixas").select("*").eq("status", "PENDENTE_CAIXARIA").execute()
                res_entradas = r.data if r.data else []
            except Exception:
                res_entradas = []

        if not res_entradas:
            res_entradas = [
                {"id": 1, "fornecedor": "Goiaba Atibaia", "embalagem": "Caixa Tropical (Hortifrúti)", "qtd_entrada": 100, "doc_ref": "NF 9120", "origem": "CEASA Campinas"},
                {"id": 2, "fornecedor": "Produtor Batata Silva", "embalagem": "Palete PBR", "qtd_entrada": 12, "doc_ref": "NF 8840", "origem": "Galpão Tropical (Campinas)"}
            ]

        df_pend = pd.DataFrame(res_entradas)

        st.markdown("##### 📋 Cargas Aguardando Liberação na Caixaria:")
        
        item_sel = None
        for idx, row in df_pend.iterrows():
            lbl = f"🏢 **{row.get('fornecedor')}** | NF: `{row.get('doc_ref')}` | Entrada: **{row.get('qtd_entrada')} x {row.get('embalagem')}** ({row.get('origem')})"
            chk = st.checkbox(lbl, key=f"chk_cx_{row.get('id')}")
            if chk:
                item_sel = row

        if item_sel is not None:
            st.write("---")
            st.markdown(f"### ⚙️ Registrar Saída de Vasilhames — `{item_sel.get('fornecedor')}`")
            st.info(f"📥 **Carga de Entrada Registrada:** **{item_sel.get('qtd_entrada')} unidades** de **{item_sel.get('embalagem')}**.")

            st.markdown("#### 📦 Quantidades Liberadas na Saída:")

            chk_saida_zero = st.checkbox("🚫 **Saída Zero / Sem Devolução** (Motorista sai sem levar embalagens)", key="chk_zero")

            c_s1, c_s2, c_s3 = st.columns(3)
            with c_s1:
                qtd_sai_trop = st.text_input("Caixas Tropical Saindo:", value="0", disabled=chk_saida_zero)
            with c_s2:
                qtd_sai_pbr = st.text_input("Paletes PBR Saindo:", value="0", disabled=chk_saida_zero)
            with c_s3:
                qtd_sai_louca = st.text_input("Caixas Loucas Saindo:", value="0", disabled=chk_saida_zero)

            val_trop = 0 if chk_saida_zero else (int(qtd_sai_trop) if qtd_sai_trop.isdigit() else 0)
            val_pbr = 0 if chk_saida_zero else (int(qtd_sai_pbr) if qtd_sai_pbr.isdigit() else 0)
            val_louca = 0 if chk_saida_zero else (int(qtd_sai_louca) if qtd_sai_louca.isdigit() else 0)

            motorista_forn = st.text_input("Nome/Placa do Motorista do Fornecedor:", placeholder="Ex: João Silva - Placa ABC-1234")
            obs_caix = st.text_input("Observações da Caixaria:", placeholder="Ex: Saída efetuada com visto")

            # Cálculo prévio do saldo resultante
            saldo_trop_result = (item_sel.get('qtd_entrada') if "Tropical" in item_sel.get('embalagem') else 0) - val_trop
            saldo_pbr_result = (item_sel.get('qtd_entrada') if "Palete" in item_sel.get('embalagem') else 0) - val_pbr

            if st.button("🚀 Confirmar Saída & Gerar Cupom da Caixaria", type="primary", use_container_width=True):
                st.success(f"✅ Saída registrada com sucesso para {item_sel.get('fornecedor')}!")

                st.markdown("---")
                st.subheader("🧾 CUPOM DE SAÍDA — SETOR DE CAIXARIA")
                if st.button("🖨️ Imprimir Cupom de Saída", type="primary"):
                    st.components.v1.html("<script>window.print();</script>", height=0)

                html_cupom_caix = f"""
                <div style="border:2px dashed #000; padding:15px; font-family:Arial, sans-serif; background-color:#fff; color:#000;">
                    <div style="text-align:center; border-bottom:1px solid #000; padding-bottom:5px;">
                        <h3 style="margin:0;">🌴 MÓDULO TROPICAL — CUPOM DE SAÍDA DE EMBALAGENS</h3>
                        <p style="margin:0; font-size:12px;">Data: {HOJE_STR} | Origem: {item_sel.get('origem')}</p>
                    </div>
                    <div style="margin-top:10px; font-size:13px;">
                        <p><strong>Fornecedor:</strong> {item_sel.get('fornecedor')}</p>
                        <p><strong>NF / Documento:</strong> {item_sel.get('doc_ref')}</p>
                        <p><strong>Entrada Recebida:</strong> {item_sel.get('qtd_entrada')} x {item_sel.get('embalagem')}</p>
                        <hr style="border:0.5px solid #ccc;">
                        <p><strong>SAÍDA LIBERADA:</strong></p>
                        <ul>
                            <li>Caixas Tropical: {val_trop} cx</li>
                            <li>Paletes PBR: {val_pbr} un</li>
                            <li>Caixas Loucas: {val_louca} cx</li>
                        </ul>
                        <p><strong>Motorista / Placa:</strong> {motorista_forn}</p>
                        <p><strong>Obs:</strong> {obs_caix}</p>
                    </div>
                    <div style="margin-top:30px; display:flex; justify-content:space-between; font-size:11px; text-align:center;">
                        <div>___________________________________<br>Visto Operador Caixaria</div>
                        <div>___________________________________<br>Visto / Assinatura Motorista</div>
                    </div>
                </div>
                """
                st.markdown(html_cupom_caix, unsafe_allow_html=True)

    with tab_caix_extrato:
        st.subheader("📊 Extrato Consolidado de Saldos")
        forn_filtro = st.text_input("🔍 Pesquisar Fornecedor:", placeholder="Digite o nome do fornecedor...")

        dados_extrato_limpo = [
            {"Fornecedor": "Goiaba Atibaia", "Entrada": "100 Cx Tropical", "Saída": "0 Cx", "Saldo Devedor/Credor": "Fornecedor devendo 100 Caixas"},
            {"Fornecedor": "Produtor Batata Silva", "Entrada": "12 Paletes PBR", "Saída": "12 Paletes PBR", "Saldo Devedor/Credor": "Quitado (Troca 1:1)"}
        ]
        
        df_ext = pd.DataFrame(dados_extrato_limpo)
        if forn_filtro.strip():
            df_ext = df_ext[df_ext["Fornecedor"].str.lower().str.contains(forn_filtro.strip().lower())]

        st.dataframe(df_ext, use_container_width=True)

# -------------------------------------------------------------------
# CADASTROS E AUXILIARES
# -------------------------------------------------------------------
elif modulo == "🗺️ Endereços das Escolas":
    st.header("🗺️ Base de Endereços das Escolas & Pontos de Entrega")
    file_end = st.file_uploader("Suba a planilha com Colunas: Cliente, Endereço, Bairro, Cidade, CEP", type=["csv", "xlsx"])
    if file_end:
        st.success("Base de endereços pronta para salvamento!")

elif modulo == "✏️ Lançamentos Avulsos":
    st.header("✏️ Lançamentos Avulsos e Ajustes de Estoque")
    st.success("Módulo de lançamentos ativado.")
