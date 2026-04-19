<div align="center">
  <img src="https://raw.githubusercontent.com/by-BC/unificador-dados-contabeis/main/assets/logo.png" width="250" alt="Analisegroup Logo">

  <h3 style="color: #C5A059; text-transform: uppercase; letter-spacing: 2px;">BPO Financeiro & Auditoria Digital</h3>

  <p align="center">
    <strong>Unificador de Extratos OFX e Motor de Conciliação Automatizada</strong>
    <br />
    Uma ferramenta de inteligência contábil para tratamento de dados, auditoria de fluxo de caixa e integração direta com sistemas de grande porte.
  </p>

  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=C5A059"></a>
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-000000?style=for-the-badge&logo=streamlit&logoColor=C5A059"></a>
  <a href="https://pandas.pydata.org/"><img src="https://img.shields.io/badge/Pandas-000000?style=for-the-badge&logo=pandas&logoColor=C5A059"></a>
  <br><a href="#"><img src="https://img.shields.io/badge/Status-Produção-000000?style=for-the-badge&logoColor=C5A059&color=C5A059"></a>
</div>

---

## 💎 Visão Executiva

O **Workspace de Conciliação Analisegroup** foi projetado para solucionar o gargalo de tempo na auditoria de BPO Financeiro. Ele abandona a verificação manual e utiliza cruzamento lógico para unificar a "Verdade do Banco" (Extratos OFX) com a "Verdade da Empresa" (Controle Interno/ERP), gerando exportações padronizadas prontas para importação contábil.

### 🎯 Principais Funcionalidades

* **🧠 Motor de Match Blindado:** Algoritmo de cruzamento que avalia o valor absoluto combinado a uma **Janela de Tempo de 3 dias**, eliminando falsos positivos decorrentes de compensação bancária em finais de semana.
* **🔄 Detecção de Transferências Internas:** Identificação autônoma de saídas e entradas de mesmo valor e data entre contas do mesmo titular, removendo distorções do saldo líquido.
* **🔍 Filtros Reativos de Auditoria:** Painel de Business Intelligence (BI) permitindo ao contador focar a triagem por Banco, Categoria ou Tipo de transação em tempo real.
* **⚙️ Integração Contábil Direta:** Conversão do modelo gerencial para o padrão de importação **Domínio Sistemas (TXT)**, com mapeamento automático de partidas dobradas (Contas 100, 300 e 400) e formatação `windows-1252`.
* **🔒 Governança e Segurança:** Sistema protegido por credenciais (`st.secrets`), painel sem retenção de dados em nuvem e rastreabilidade total (coluna `Arquivo_Origem` indicando a proveniência exata de cada linha).

---

## 📐 Arquitetura de Dados

O fluxo de processamento foi desenhado para garantir 100% de confiabilidade na geração do arquivo final:

1. **Ingestão (Upload):** Múltiplos arquivos `.OFX` (Bancos diversos) + Arquivo `.CSV/.XLSX` (ERP do cliente).
2. **Data Cleaning:** Parser extrai Data, Valor, Tipo e lê a string de histórico aplicando RegEx para extração de CNPJ (14 dígitos).
3. **Categorização Dinâmica:** Dicionário de palavras-chave identifica instantaneamente a natureza da transação (Ex: "DARF" -> Impostos).
4. **Triagem Lógica:** Divisão dos dados em abas (Conciliados, Pendentes e Transferências).
5. **Data Visualization:** Gráficos interativos renderizados via Plotly, incluindo Tendência de Fluxo de Caixa Mensal (linhas *spline*).

---

## 🚀 Como Executar o Projeto (Localmente)

### 1. Pré-requisitos
Certifique-se de ter o Python 3.9+ instalado em sua máquina.

### 2. Clonando o Repositório
```bash
git clone [https://github.com/by-BC/unificador-dados-contabeis.git](https://github.com/by-BC/unificador-dados-contabeis.git)
cd unificador-dados-contabeis
