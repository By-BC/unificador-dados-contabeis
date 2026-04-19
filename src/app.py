import streamlit as st
import pandas as pd
from ofxparse import OfxParser
import re
from io import StringIO

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="Analisegroup | Unificador", page_icon="📊", layout="wide")

def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Interface de login
    st.title("🔐 Acesso Restrito - Analisegroup")
    password = st.text_input("Insira a senha de acesso", type="password")
    
    if st.button("Entrar"):
        if password == "Analise2026": # Escolha sua senha aqui
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

if not check_password():
    st.stop()  # Trava o app aqui se não estiver logado

# --- LÓGICA DE NEGÓCIO (Suas Regras) ---
BANCOS_MAPEADOS = {
    '001': 'Banco do Brasil', '004': 'Banco do Nordeste', 
    '074': 'Banco Safra', '104': 'Caixa Econômica Federal', 
    '237': 'Bradesco', '382': 'Tribanco'
}

def extrair_cnpj(memo):
    if not memo: return ""
    numeros = re.sub(r'[^0-9]', '', memo)
    if len(numeros) >= 14:
        match = re.search(r'\d{14}', numeros)
        if match:
            cnpj = match.group(0)
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return ""

def processar_arquivos(arquivos_carregados):
    todos_os_dados = []
    for arquivo in arquivos_carregados:
        ofx = OfxParser.parse(arquivo)
        banco_id = ofx.account.routing_number
        nome_banco = BANCOS_MAPEADOS.get(banco_id, f"Banco {banco_id}")
        
        for transacao in ofx.account.statement.transactions:
            valor = float(transacao.amount)
            todos_os_dados.append({
                'Arquivo': arquivo.name,
                'Data': transacao.date.strftime('%d/%m/%Y'),
                'Banco': nome_banco,
                'Valor': valor,
                'Tipo': 'CREDITO' if valor >= 0 else 'DEBITO',
                'CNPJ': extrair_cnpj(transacao.memo),
                'Histórico': transacao.memo
            })
    return pd.DataFrame(todos_os_dados)

# --- INTERFACE (UI) ---
st.title("📊 Unificador de Extratos OFX")
st.subheader("Foco em Eficiência e Automação Contábil")

st.info("Arraste um ou mais arquivos .ofx para processar a consolidação automaticamente.")

# Upload de múltiplos arquivos
arquivos = st.file_uploader("Selecione os arquivos OFX", type=["ofx"], accept_multiple_files=True)

if arquivos:
    df_final = processar_arquivos(arquivos)
    
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Arquivos", len(arquivos))
    col2.metric("Total de Transações", len(df_final))
    col3.metric("Valor Total", f"R$ {df_final['Valor'].sum():,.2f}")

    # Prévia dos dados
    st.write("### 🔍 Prévia dos Dados Consolidados")
    st.dataframe(df_final, use_container_width=True)

    # --- SEÇÃO DE AUDITORIA VISUAL ---
    st.write("### 📊 Auditoria de Fluxo por Banco")

    # Agrupando dados para o gráfico
    df_grafico = df_final.groupby(['Banco', 'Tipo'])['Valor'].sum().abs().reset_index()

    # Criando colunas para os gráficos ficarem lado a lado
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("**Total por Tipo (Crédito vs Débito)**")
        st.bar_chart(df_grafico, x="Tipo", y="Valor", color="Tipo")

    with col_chart2:
        st.write("**Volume de Transações por Banco**")
        contagem_bancos = df_final['Banco'].value_counts()
        st.bar_chart(contagem_bancos)

    # Botão de Download
    csv = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    
    st.download_button(
        label="📥 Baixar Planilha Consolidada (CSV)",
        data=csv,
        file_name="analisegroup_consolidado.csv",
        mime="text/csv",
    )