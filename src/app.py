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
    
    # Criar um formulário faz com que o "Enter" funcione como o botão de envio
    with st.form("login_form", clear_on_submit=False):
        password = st.text_input("Insira a senha de acesso", type="password")
        submit_button = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit_button:
            if password == st.secrets["general"]["access_password"]:
                st.session_state["password_correct"] = True
                st.rerun() # Reinicia para liberar o app
            else:
                st.error("Senha incorreta. Tente novamente.")
                
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

# --- ÁREAS DE UPLOAD (A DUPLA PONTA DA CONCILIAÇÃO) ---
st.markdown("### 📥 Entrada de Dados (Preparação para o Match)")
col_up1, col_up2 = st.columns(2)

with col_up1:
    st.markdown("<p style='color:#C5A059; font-weight:bold; margin-bottom:0;'>1. A Verdade do Banco</p>", unsafe_allow_html=True)
    arquivos_ofx = st.file_uploader("Extratos OFX (Múltiplos)", type=["ofx"], accept_multiple_files=True)

with col_up2:
    st.markdown("<p style='color:#C5A059; font-weight:bold; margin-bottom:0;'>2. A Verdade da Empresa</p>", unsafe_allow_html=True)
    arquivo_erp = st.file_uploader("Controle Interno (CSV ou Excel)", type=["csv", "xlsx"])
    
    valores_erp = [] # Lista que vai guardar os valores do cliente
    if arquivo_erp:
        try:
            # Controle lógico para aceitar tanto CSV quanto Excel
            if arquivo_erp.name.endswith('.csv'):
                df_erp = pd.read_csv(arquivo_erp, sep=';', decimal=',')
            else:
                df_erp = pd.read_excel(arquivo_erp)
            
            # Busca a coluna de Valor (independente se está maiúscula ou minúscula)
            coluna_valor = [col for col in df_erp.columns if 'VALOR' in str(col).upper()]
            
            if coluna_valor:
                # Transforma todos os valores em absolutos para facilitar o match
                valores_erp = df_erp[coluna_valor[0]].abs().tolist()
                st.success(f"✅ ERP carregado! {len(valores_erp)} lançamentos prontos para auditoria.")
            else:
                st.error("A planilha precisa ter uma coluna chamada 'Valor'.")
        except Exception as e:
            st.error(f"Erro na leitura do arquivo: {e}")

st.markdown("---")

# --- MAPEAMENTO DE BANCOS (Atualizado) ---
BANCOS_MAPEADOS = {
    '1': 'Banco do Brasil',
    '33': 'Santander',
    '104': 'Caixa Econômica',
    '237': 'Bradesco',
    '341': 'Itaú',
    '77': 'Inter',
    '260': 'Nubank',
    '634': 'Tribanco', # Banco Triângulo
    '382': 'Tribanco', # Outro código comum do Tribanco
    '41': 'Banrisul',
    '422': 'Banco Safra',
    '74': 'Banco Safra'
}

# --- INTELIGÊNCIA DE CATEGORIZAÇÃO (PLANO DE CONTAS BPO) ---
REGRAS_CATEGORIZACAO = {
    'TARIFA': 'Despesas Bancárias',
    'MANUT': 'Despesas Bancárias',
    'PIX': 'Transferências Pix',
    'TED': 'Transferências',
    'DOC': 'Transferências',
    'PAGTO COBRANCA': 'Pagamento de Fornecedores',
    'PAGTO TITULO': 'Pagamento de Fornecedores',
    'DARF': 'Impostos',
    'GPS': 'Impostos',
    'SIMPLES NAC': 'Impostos',
    'SALA': 'Folha de Pagamento',
    'REND PAGO': 'Rendimentos de Aplicação',
    'IOF': 'Impostos Financeiros',
    'SAQUE': 'Saques em Espécie'
}

def categorizar_transacao(historico):
    hist_upper = str(historico).upper()
    for palavra_chave, categoria in REGRAS_CATEGORIZACAO.items():
        if palavra_chave in hist_upper:
            return categoria
    return 'Não Categorizado (Pendente)'

if arquivos_ofx:
    dados = []
    for f in arquivos_ofx:
        ofx = OfxParser.parse(f)
        
        codigo_raw = str(ofx.account.routing_number).strip()
        codigo_limpo = codigo_raw.lstrip('0')
        nome_banco = BANCOS_MAPEADOS.get(codigo_limpo, f"Banco {codigo_raw}")
        
        for t in ofx.account.statement.transactions:
            v = float(t.amount)
            dados.append({
                'Banco': nome_banco, 
                'Data': t.date, 
                'Valor': v, 
                'Tipo': 'CREDITO' if v >= 0 else 'DEBITO',
                'Categoria': categorizar_transacao(t.memo), # A MÁGICA ACONTECE AQUI
                'CNPJ': extrair_cnpj(t.memo), 
                'Histórico': t.memo
            })
    
    df = pd.DataFrame(dados)
    
    # --- MOTOR DE MATCH (CONTROLE LÓGICO DE CONCILIAÇÃO) ---
    if valores_erp:
        # Criamos uma cópia da fila do ERP para ir "dando baixa"
        fila_erp = valores_erp.copy()
        status_match = []
        
        # Percorre cada linha do Banco (OFX)
        for valor_banco in df['Valor'].abs():
            match_encontrado = False
            
            # Tenta encontrar o valor exato na fila do ERP
            for valor_cliente in fila_erp:
                # Usamos uma margem mínima (0.01) para evitar erros de arredondamento do Python
                if abs(valor_banco - valor_cliente) < 0.01:
                    status_match.append('✅ Conciliado')
                    fila_erp.remove(valor_cliente) # Consome o valor para não dar match duplo
                    match_encontrado = True
                    break # Para de procurar e vai para a próxima linha do banco
            
            if not match_encontrado:
                status_match.append('❌ Pendente no ERP')
                
        df['Status'] = status_match
    else:
        # Se não enviou o ERP, fica tudo aguardando
        df['Status'] = '⚠️ Aguardando ERP'
        

    # --- 1. LÓGICA DE CONCILIAÇÃO (Roda primeiro nos bastidores) ---
    df_cruzamento = df.copy()
    df_cruzamento['Valor_Abs'] = df_cruzamento['Valor'].abs()
    grupos = df_cruzamento.groupby(['Data', 'Valor_Abs'])
    
    lista_transferencias = []
    for nome, grupo in grupos:
        if len(grupo) >= 2:
            if 'CREDITO' in grupo['Tipo'].values and 'DEBITO' in grupo['Tipo'].values:
                lista_transferencias.append(grupo)
                
    tem_transferencias = len(lista_transferencias) > 0
    if tem_transferencias:
        df_transferencias = pd.concat(lista_transferencias).drop(columns=['Valor_Abs'])

    # --- 2. AÇÕES RÁPIDAS (Botões de Download no Topo) ---
    st.write("### 📥 Ações Rápidas")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        csv_consolidado = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📄 Baixar Planilha Consolidada", data=csv_consolidado, file_name="analisegroup_consolidado.csv", mime="text/csv", use_container_width=True)
        
    with col_btn2:
        if tem_transferencias:
            csv_transf = df_transferencias.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="🔄 Baixar Relatório de Transferências", data=csv_transf, file_name="analisegroup_transferencias.csv", mime="text/csv", use_container_width=True)
        else:
            st.button("✅ Sem transferências internas", disabled=True, use_container_width=True)

    st.markdown("---")

    # --- 3. PAINEL DE TRIAGEM E AUDITORIA (A PLANILHA FOI MOVIDA PARA CÁ) ---
    st.write("### 🔍 Triagem de Conciliação (Auditoria)")
    df_tela = df.copy()
    df_tela['Valor'] = df_tela['Valor'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    if valores_erp:
        total_banco = len(df)
        conciliados = len(df[df['Status'] == '✅ Conciliado'])
        pendentes = len(df[df['Status'] == '❌ Pendente no ERP'])
        taxa = (conciliados / total_banco) * 100 if total_banco > 0 else 0

        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; background-color: #1A1A1A; padding: 15px; border-radius: 8px; border-left: 5px solid #C5A059; margin-bottom: 20px;'>
            <div><span style='color: #F0F0F0;'>Lançamentos no Banco:</span> <b style='color: #C5A059; font-size: 18px;'>{total_banco}</b></div>
            <div><span style='color: #F0F0F0;'>✅ Conciliados (Match):</span> <b style='color: #00CC66; font-size: 18px;'>{conciliados}</b></div>
            <div><span style='color: #F0F0F0;'>❌ Pendentes:</span> <b style='color: #FF4B4B; font-size: 18px;'>{pendentes}</b></div>
            <div><span style='color: #F0F0F0;'>🎯 Taxa de Sucesso:</span> <b style='color: #C5A059; font-size: 18px;'>{taxa:.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["⚠️ Exigem Atenção (Pendentes)", "✅ Tudo Certo (Conciliados)", "📋 Visão Geral (Todos)"])
        with tab1: st.dataframe(df_tela[df_tela['Status'] == '❌ Pendente no ERP'], use_container_width=True)
        with tab2: st.dataframe(df_tela[df_tela['Status'] == '✅ Conciliado'], use_container_width=True)
        with tab3: st.dataframe(df_tela, use_container_width=True)
    else:
        st.dataframe(df_tela, use_container_width=True)

    st.write("---")

    # --- 4. BLOCO DE KPIs (Resumo Executivo) ---
    total_credito = df[df['Tipo'] == 'CREDITO']['Valor'].sum()
    total_debito = abs(df[df['Tipo'] == 'DEBITO']['Valor'].sum())
    saldo_liquido = total_credito - total_debito
    cor_saldo = "#C5A059" if saldo_liquido >= 0 else "#FF4B4B"

    st.write("### 💎 Resumo Executivo")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1: st.markdown(f"<div style='border: 1px solid #C5A059; padding: 20px; border-radius: 10px; text-align: center;'> <p style='margin:0; color:#F0F0F0; text-transform:uppercase; font-size:12px; letter-spacing:2px;'>Total Créditos</p> <h2 style='margin:0; color:#C5A059;'>R$ {total_credito:,.2f}</h2> </div>", unsafe_allow_html=True)
    with kpi2: st.markdown(f"<div style='border: 1px solid #5C4A26; padding: 20px; border-radius: 10px; text-align: center;'> <p style='margin:0; color:#F0F0F0; text-transform:uppercase; font-size:12px; letter-spacing:2px;'>Total Débitos</p> <h2 style='margin:0; color:#F0F0F0;'>R$ {total_debito:,.2f}</h2> </div>", unsafe_allow_html=True)
    with kpi3: st.markdown(f"<div style='background-color: rgba(197, 160, 89, 0.1); border: 2px solid {cor_saldo}; padding: 20px; border-radius: 10px; text-align: center;'> <p style='margin:0; color:#F0F0F0; text-transform:uppercase; font-size:12px; letter-spacing:2px;'>Saldo Líquido</p> <h2 style='margin:0; color:{cor_saldo};'>R$ {saldo_liquido:,.2f}</h2> </div>", unsafe_allow_html=True)

    st.write("---")

    # --- 5. ANÁLISE DETALHADA POR INSTITUIÇÃO ---
    st.write("### 🏦 Detalhamento por Banco")
    c1, c2 = st.columns(2)

    with c1:
        st.write("#### 💰 Volume Financeiro Total")
        df_vol_banco = df.groupby('Banco')['Valor'].apply(lambda x: x.abs().sum()).reset_index()
        df_vol_banco = df_vol_banco.sort_values('Valor', ascending=False)
        fig1 = px.bar(df_vol_banco, x='Banco', y='Valor', text='Valor', color='Banco', color_discrete_sequence=['#C5A059', '#E2BC7A', '#8E794E', '#5C4A26'], template="plotly_dark")
        fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside', cliponaxis=False)
        fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, yaxis_visible=False, xaxis_title=None, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.write("#### 📊 Frequência de Transações")
        df_banco_count = df['Banco'].value_counts().reset_index()
        fig2 = px.pie(df_banco_count, values='count', names='Banco', color_discrete_sequence=['#C5A059', '#E2BC7A', '#8E794E', '#5C4A26'], template="plotly_dark", hole=.6)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, b=0, l=0, r=0))
        fig2.update_traces(textinfo='percent+label', pull=[0.05 if i == 0 else 0 for i in range(len(df_banco_count))])
        st.plotly_chart(fig2, use_container_width=True)

    st.write("---")

    # --- 6. AUDITORIA DE TRANSFERÊNCIAS (Ficou no final como anexo visual) ---
    if tem_transferencias:
        st.write("### 🔄 Alerta de Transferências Internas")
        st.markdown("<p style='color: #C5A059; font-size: 14px;'><i>Possíveis movimentações entre contas da mesma titularidade.</i></p>", unsafe_allow_html=True)
        df_transferencias_tela = df_transferencias.copy()
        df_transferencias_tela['Valor'] = df_transferencias_tela['Valor'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.dataframe(df_transferencias_tela, use_container_width=True)
        st.info("💡 Estas transações anulam umas às outras no Saldo Líquido.")