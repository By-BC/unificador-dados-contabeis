import streamlit as st
import pandas as pd
from ofxparse import OfxParser
import re
import plotly.express as px

# --- CONFIGURAÇÃO E TEMA ---
st.set_page_config(page_title="Analisegroup | Unificador", page_icon="📊", layout="wide")

# CSS Blindado - Estética Analisegroup (Preto e Dourado)
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0A0A0A !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #F0F0F0 !important; }
    
    /* Botões com Gradiente Dourado */
    div.stButton > button, div.stDownloadButton > button, section[data-testid="stFileUploader"] section button {
        background-image: linear-gradient(135deg, #E2BC7A 0%, #C5A059 100%) !important;
        color: #000000 !important; 
        border: none !important; 
        font-weight: 800 !important; 
        text-transform: uppercase;
        border-radius: 8px !important;
    }
    
    /* Área de Upload */
    section[data-testid="stFileUploader"] { 
        background-color: #1A1A1A !important; 
        border: 1px dashed #C5A059 !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE SEGURANÇA (GOVERNANÇA DE TI) ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    
    st.title("🔐 Acesso Restrito - Analisegroup")
    password = st.text_input("Insira a senha de acesso", type="password")
    
    if st.button("Entrar"):
        # IMPORTANTE: st.secrets["general"]["access_password"] substitui a senha fixa
        # Você definirá o valor real desta senha no painel do Streamlit Cloud
        if password == st.secrets["general"]["access_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

if not check_password():
    st.stop()

# --- LÓGICA DE NEGÓCIO ---
def extrair_cnpj(memo):
    numeros = re.sub(r'[^0-9]', '', str(memo))
    if len(numeros) >= 14:
        match = re.search(r'\d{14}', numeros)
        if match:
            c = match.group(0)
            return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"
    return ""

# --- INTERFACE ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    st.image("assets/logo.png", width=110)
with col_text:
    st.write("# Unificador de Extratos OFX")
    st.write("*Uma Contabilidade de Excelência*")

st.markdown("---")
arquivos = st.file_uploader("Selecione os arquivos OFX", type=["ofx"], accept_multiple_files=True)

if arquivos:
    dados = []
    for f in arquivos:
        ofx = OfxParser.parse(f)
        for t in ofx.account.statement.transactions:
            v = float(t.amount)
            dados.append({
                'Banco': ofx.account.routing_number, 
                'Data': t.date, 
                'Valor': v, 
                'Tipo': 'CREDITO' if v >= 0 else 'DEBITO', 
                'CNPJ': extrair_cnpj(t.memo), 
                'Histórico': t.memo
            })
    
    df = pd.DataFrame(dados)
    
    st.write("### 📊 Auditoria de Fluxo")
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.bar(df.groupby('Tipo')['Valor'].sum().abs().reset_index(), x='Tipo', y='Valor', color='Tipo', color_discrete_map={'CREDITO': '#C5A059', 'DEBITO': '#7A6337'}, template="plotly_dark")
        fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.pie(df['Banco'].value_counts().reset_index(), values='count', names='Banco', color_discrete_sequence=['#C5A059', '#E2BC7A'], template="plotly_dark")
        fig2.update_traces(hole=.4)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    # --- FORMATAÇÃO BRASILEIRA PARA TELA E EXCEL ---
    st.write("### 🔍 Prévia dos Dados")
    
    # 1. Criamos uma cópia apenas para a visualização na tela
    df_tela = df.copy()
    
    # 2. Aplicamos a máscara brasileira (troca ponto por vírgula e vírgula por ponto)
    # Exemplo: 1234.56 vira 1.234,56
    df_tela['Valor'] = df_tela['Valor'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    # Mostra a tabela na interface
    st.dataframe(df_tela, use_container_width=True)

    # 3. Conversão para download com o parâmetro mágico: decimal=','
    # Isso garante que o Excel brasileiro entenda a coluna Valor como dinheiro/número nativo
    csv = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig').encode('utf-8-sig')
    
    st.download_button(
        label="📥 Baixar Planilha Consolidada", 
        data=csv, 
        file_name="analisegroup_consolidado.csv", 
        mime="text/csv"
    )