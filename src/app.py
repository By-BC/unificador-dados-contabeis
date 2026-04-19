import streamlit as st
import pandas as pd
import plotly.express as px
from ofxparse import OfxParser
import io
import re

# --- CONFIGURAÇÃO DA PÁGINA (CLEAN & PREMIUM) ---
st.set_page_config(
    page_title="Analisegroup | Financial Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed" # Esconde a sidebar por padrão
)

# --- INJEÇÃO DE CSS (ALTA COSTURA DIGITAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap');
    
    /* Fundo e Fonte Geral */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
        background-color: #000000; /* Preto Absoluto */
        color: #FFFFFF;
    }

    /* Escondendo Elementos Padrão */
    [data-testid="stHeader"], [data-testid="stSidebar"], footer {display: none !important;}
    
    /* Header de Luxo Centrado */
    .main-header {
        text-align: center;
        padding: 40px 0 20px 0;
        border-bottom: 1px solid rgba(197, 160, 89, 0.2);
        margin-bottom: 40px;
    }
    
    .main-header img {
        width: 220px;
        margin-bottom: 15px;
    }

    /* Cartões de KPI com Borda Dourada Fina */
    div[data-testid="stMetric"] {
        background: #0A0A0A !important;
        border: 1px solid #1A1A1A !important;
        border-bottom: 3px solid #C5A059 !important; /* Detalhe em ouro */
        border-radius: 4px !important;
        padding: 15px !important;
    }

    /* Botões com Gradiente Metálico */
    .stButton > button {
        width: 100%;
        background: linear-gradient(145deg, #C5A059, #8E794E) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 2px !important; /* Bordas secas são mais profissionais */
        font-weight: 600 !important;
        letter-spacing: 2px !important;
        padding: 12px !important;
        transition: 0.4s !important;
    }
    
    .stButton > button:hover {
        background: #FFFFFF !important;
        color: #000 !important;
        box-shadow: 0 0 20px rgba(197, 160, 89, 0.4);
    }

    /* Estilização das Tabelas (Dataframes) */
    .stDataFrame {
        border: 1px solid #1A1A1A !important;
        border-radius: 8px !important;
    }

    /* Inputs de Senha e Texto */
    .stTextInput input {
        background-color: #0A0A0A !important;
        color: #C5A059 !important;
        border: 1px solid #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO DA MARCA ---
st.markdown(f"""
    <div class="main-header">
        <img src="https://raw.githubusercontent.com/bruno-candido/unificador-dados-contabeis/main/assets/logo.png" onerror="this.src='https://via.placeholder.com/220x80/000000/C5A059?text=ANALISEGROUP'">
        <p style="color: #C5A059; letter-spacing: 5px; font-size: 12px; font-weight: 300; margin-top: -10px;">
            BPO FINANCEIRO & AUDITORIA DIGITAL
        </p>
    </div>
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
    
    fila_erp = [] # Agora vai guardar um "dicionário" com Data e Valor
    if arquivo_erp:
        try:
            if arquivo_erp.name.endswith('.csv'):
                df_erp = pd.read_csv(arquivo_erp, sep=';', decimal=',')
            else:
                df_erp = pd.read_excel(arquivo_erp)
            
            coluna_valor = [col for col in df_erp.columns if 'VALOR' in str(col).upper()]
            coluna_data = [col for col in df_erp.columns if 'DATA' in str(col).upper()]
            
            if coluna_valor and coluna_data:
                # O Faxineiro de Valores
                def limpar_numero(x):
                    try:
                        if pd.isna(x): return None
                        if isinstance(x, (int, float)): return float(x)
                        x_str = str(x).upper().replace('R$', '').strip()
                        if ',' in x_str: x_str = x_str.replace('.', '').replace(',', '.')
                        return float(x_str)
                    except: return None 
                
                # Prepara as duas colunas: Valor e Data
                df_erp['Valor_Limpo'] = df_erp[coluna_valor[0]].apply(limpar_numero)
                df_erp['Data_Parsed'] = pd.to_datetime(df_erp[coluna_data[0]], errors='coerce')
                
                # Remove linhas vazias e cria a fila de pendências do ERP
                df_erp_valido = df_erp.dropna(subset=['Valor_Limpo', 'Data_Parsed'])
                
                # Transforma em uma lista de registros (Data e Valor) para o Match
                fila_erp = df_erp_valido[['Data_Parsed', 'Valor_Limpo']].to_dict('records')
                
                st.success(f"✅ ERP carregado! {len(fila_erp)} lançamentos com Data e Valor prontos.")
            else:
                st.error("A planilha do ERP precisa ter as colunas 'Data' e 'Valor'.")
        except Exception as e:
            st.error(f"Erro na leitura do arquivo: {e}")

st.markdown("---")

# --- ESCUDO DE PROTEÇÃO (Garante que o sistema não quebre por falta de arquivos) ---
if not arquivos_ofx:
    st.info("👆 Por favor, anexe os extratos OFX para iniciar a auditoria.")
    st.stop() # Para a execução do aplicativo aqui até que o arquivo seja enviado

if not fila_erp:
    st.warning("⚠️ Operando apenas com a Verdade do Banco. Anexe o Controle Interno (ERP) para habilitar o Motor de Match.")
    # Aqui NÃO usamos st.stop() porque o contador pode querer apenas o consolidador de OFX

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
    
    # --- MOTOR DE MATCH (Valor exato + Janela de 3 dias) ---
    if fila_erp:
        status_match = []
        # Garante que a data do banco seja um formato de data reconhecido
        df['Data_Parsed'] = pd.to_datetime(df['Data'], errors='coerce')
        
        for idx, row in df.iterrows():
            valor_banco = abs(row['Valor'])
            data_banco = row['Data_Parsed']
            match_encontrado = False
            
            # Só tenta cruzar se tiver uma data válida no banco
            if pd.notnull(data_banco):
                for item_erp in fila_erp:
                    valor_cliente = abs(item_erp['Valor_Limpo'])
                    data_cliente = item_erp['Data_Parsed']
                    
                    # 1. Bateu o valor?
                    if abs(valor_banco - valor_cliente) < 0.01:
                        # 2. Bateu a data? (Tolerância de até 3 dias de diferença)
                        diferenca_dias = abs((data_banco - data_cliente).days)
                        if diferenca_dias <= 3:
                            status_match.append('✅ Conciliado')
                            fila_erp.remove(item_erp) # Tira da fila para não dar match duplo
                            match_encontrado = True
                            break # Para de procurar
            
            if not match_encontrado:
                status_match.append('❌ Pendente no ERP')
                
        df['Status'] = status_match
        df = df.drop(columns=['Data_Parsed']) # Limpa a coluna auxiliar
    else:
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

    # --- 2. AÇÕES RÁPIDAS E EXPORTAÇÃO CONTÁBIL ---
    st.write("### 📥 Ações Rápidas e Integração")
    
    # Seletor de Sistema Contábil com estilo premium
    st.markdown("<p style='color:#C5A059; font-size:14px; margin-bottom:5px;'>Selecione o formato de saída dos dados:</p>", unsafe_allow_html=True)
    sistema_escolhido = st.radio(
        "Formato de Exportação", 
        ["Padrão Analisegroup (CSV Gerencial)", "Domínio Sistemas (TXT Contábil)"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    st.write("") # Espaçamento
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if sistema_escolhido == "Domínio Sistemas (TXT Contábil)":
            # --- MÁGICA DE TRADUÇÃO PARA DOMÍNIO ---
            df_export = df.copy()
            
            # Simulando o Plano de Contas Padrão (De-Para)
            # Banco = 100 | Despesa = 400 | Receita = 300
            df_export['Conta_Debito'] = df_export.apply(lambda x: 100 if x['Tipo'] == 'CREDITO' else 400, axis=1)
            df_export['Conta_Credito'] = df_export.apply(lambda x: 300 if x['Tipo'] == 'CREDITO' else 100, axis=1)
            
            # Formata a Data para o padrão exato do Domínio (DD/MM/YYYY)
            df_export['Data_Formatada'] = pd.to_datetime(df_export['Data']).dt.strftime('%d/%m/%Y')
            
            # Cria a estrutura final exigida pelo layout do sistema
            df_dominio = df_export[['Data_Formatada', 'Conta_Debito', 'Conta_Credito', 'Valor', 'Histórico']]
            df_dominio.columns = ['Data', 'Conta_Debito', 'Conta_Credito', 'Valor', 'Historico']
            
            # Domínio geralmente aceita TXT separado por ponto e vírgula e codificação Windows (ANSI)
            arquivo_final = df_dominio.to_csv(index=False, sep=';', decimal=',', encoding='windows-1252').encode('windows-1252')
            nome_arq = "analisegroup_importacao_dominio.txt"
            mime_tipo = "text/plain"
            icone_botao = "⚙️ Baixar TXT para Domínio"
            
        else:
            # --- PADRÃO GERENCIAL ANALISEGROUP ---
            arquivo_final = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig').encode('utf-8-sig')
            nome_arq = "analisegroup_consolidado.csv"
            mime_tipo = "text/csv"
            icone_botao = "📄 Baixar Planilha Consolidada"

        # O botão dinâmico
        st.download_button(
            label=icone_botao, 
            data=arquivo_final, 
            file_name=nome_arq, 
            mime=mime_tipo, 
            use_container_width=True
        )
        
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

    if fila_erp:
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