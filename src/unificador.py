# Importa o módulo 'os', usado para interagir com o sistema operacional (manipular caminhos, pastas, arquivos, etc.)
import os
# Importa a biblioteca 'pandas' com o apelido 'pd', que é uma ferramenta poderosa para manipulação e análise de dados (tabelas)
import pandas as pd
# Importa a classe 'OfxParser' da biblioteca 'ofxparse', que serve para ler e interpretar arquivos no formato OFX (arquivos bancários)
from ofxparse import OfxParser
# Importa o módulo 're', que fornece operações de expressões regulares, usado aqui para buscar padrões em textos (como extrair números)
import re
# Importa a classe 'datetime' do módulo 'datetime', usada para trabalhar com datas e horas
from datetime import datetime

# Dicionário de Bancos (Baseado no seu mapeamento FID)
# Este dicionário mapeia o código numérico (routing number) de cada banco para o seu nome amigável
BANCOS_MAPEADOS = {
    '001': 'Banco do Brasil',
    '004': 'Banco do Nordeste',
    '074': 'Banco Safra',
    '104': 'Caixa Econômica Federal',
    '237': 'Bradesco',
    '382': 'Tribanco'
}

def extrair_cnpj(memo):
    """Busca um padrão de 14 dígitos no texto, ignora CPFs e aplica a máscara de CNPJ."""
    # Se o texto (memo) estiver vazio ou nulo, retorna uma string vazia
    if not memo:
        return ""
    
    # Utiliza expressão regular para remover tudo que não for número (0 a 9) da descrição
    numeros = re.sub(r'[^0-9]', '', memo)
    
    # Verifica se sobraram pelo menos 14 números (o tamanho mínimo para um CNPJ)
    # Procura blocos exatos de 14 dígitos (ignorando se achar apenas 11, o que seria um CPF)
    if len(numeros) >= 14:
        # Busca especificamente uma sequência de exatamente 14 dígitos consecutivos
        match = re.search(r'\d{14}', numeros)
        if match:
            # Se encontrar a sequência, extrai o CNPJ puro (somente números)
            cnpj = match.group(0)
            # Retorna o CNPJ formatado aplicando a máscara padrão: XX.XXX.XXX/XXXX-XX
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            
    # Se não encontrar nenhum padrão de 14 dígitos, retorna vazio
    return ""

def determinar_tipo(tipo_ofx, valor):
    """Aplica a regra de ouro do seu mapeamento: o sinal do valor define o tipo real."""
    # Converte o valor da transação para número decimal (float) e verifica se é maior ou igual a zero
    if float(valor) >= 0:
        # Valores positivos ou zero são classificados como 'CREDITO'
        return 'CREDITO'
    else:
        # Valores negativos são classificados como 'DEBITO'
        return 'DEBITO'

def formatar_data(data_ofx, banco_id):
    """Aplica a regra de data específica (BB usa AA, resto usa AAAA)"""
    # Se não houver data, retorna vazio
    if not data_ofx:
        return ""
    
    # O ofxparse já converte a data do arquivo para um objeto datetime do Python automaticamente
    if banco_id == '001': # Se for o Banco do Brasil
        # Formata a data retornando Dia/Mês/Ano com 2 dígitos para o ano (ex: 24/12/23)
        return data_ofx.strftime('%d/%m/%y')
    else: # Para os demais bancos
        # Formata a data retornando Dia/Mês/Ano com 4 dígitos para o ano (ex: 24/12/2023)
        return data_ofx.strftime('%d/%m/%Y')

def ofx_to_dataframe(caminho_arquivo):
    """Lê um arquivo OFX e converte para as regras da Analisegroup, retornando um DataFrame (tabela Pandas)."""
    # Extrai apenas o nome do arquivo a partir do caminho completo (ex: 'extrato.ofx')
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    # Verifica se o arquivo termina com a extensão '.ofx' (ignorando se é letra maiúscula ou minúscula)
    if not caminho_arquivo.lower().endswith('.ofx'):
        print(f"❌ Erro: {nome_arquivo} não é um arquivo OFX válido.")
        return None

    try:
        # Abre o arquivo no modo 'rb' (leitura binária, necessário para o ofxparse ler corretamente os dados e acentos)
        with open(caminho_arquivo, 'rb') as f:
            # Faz o parse (leitura/interpretação) do conteúdo do arquivo OFX e salva na variável ofx
            ofx = OfxParser.parse(f)
    except Exception as e:
        # Se ocorrer qualquer erro na leitura do arquivo, exibe uma mensagem de erro e retorna None
        print(f"❌ Erro ao ler {nome_arquivo}: {e}")
        return None

    # Identificação do Banco: extrai o código do banco (routing_number) das informações da conta do OFX
    banco_id = ofx.account.routing_number
    # Busca o nome correspondente no nosso dicionário 'BANCOS_MAPEADOS'; se não achar, usa a frase "Banco não identificado"
    nome_banco = BANCOS_MAPEADOS.get(banco_id, "Banco não identificado")

    # Cria uma lista vazia que irá armazenar os dados extraídos de cada transação (uma lista de linhas)
    dados_extraidos = []

    # Faz um loop iterando (passando uma a uma) sobre todas as transações do extrato da conta lida no OFX
    for transacao in ofx.account.statement.transactions:
        # Converte o valor da transação para número decimal (com casas decimais)
        valor = float(transacao.amount)
        
        # Cria um dicionário chamado 'linha' contendo todas as informações formatadas dessa transação específica
        linha = {
            'nome_arquivo': nome_arquivo, # Nome do arquivo de origem, útil para auditoria
            'data': formatar_data(transacao.date, banco_id), # Chama a função formatar_data para obter a data no padrão correto
            'banco': nome_banco, # Nome amigável do banco que resolvemos antes
            'valor': valor, # Valor numérico da transação
            'tipo': determinar_tipo(transacao.type, valor), # Chama a função determinar_tipo para classificar como CREDITO/DEBITO pelo sinal
            'cnpj': extrair_cnpj(transacao.memo), # Chama a função que varre o histórico da transação em busca de um CNPJ
            'complemento_historico': transacao.memo if transacao.memo else transacao.id # Usa o histórico (memo) se existir; caso contrário, usa o ID da transação
        }
        # Adiciona o dicionário da transação à nossa lista principal
        dados_extraidos.append(linha)

    # Transforma a lista de dicionários em um DataFrame (uma tabela estruturada) do Pandas
    df = pd.DataFrame(dados_extraidos)
    # Retorna essa tabela finalizada para quem chamou a função
    return df

# --- ÁREA DE TESTE (EXECUÇÃO PRINCIPAL) ---
# A linha abaixo garante que o código abaixo só seja executado se o arquivo for rodado diretamente (e não se for importado por outro arquivo)
if __name__ == "__main__":
    # Define o caminho da pasta de onde vamos ler os arquivos de entrada
    pasta_inputs = os.path.join("data", "inputs")
    # Define o caminho da pasta onde salvaremos o arquivo de saída (a tabela consolidada final)
    pasta_saida = "data"
    
    # Cria a pasta de entradas (data/inputs), caso ela ainda não exista
    os.makedirs(pasta_inputs, exist_ok=True)
    # Cria a pasta de saída (data), caso ela ainda não exista
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Lista e guarda todos os nomes de arquivos encontrados na pasta de inputs que terminem com a extensão '.ofx'
    arquivos = [f for f in os.listdir(pasta_inputs) if f.lower().endswith('.ofx')]
    
    # Se a lista de arquivos estiver vazia, emite um aviso e nada mais é feito
    if not arquivos:
        print("⚠️ Nenhum arquivo .ofx encontrado na pasta data/inputs.")
    else:
        # Cria uma lista geral (vazia inicialmente) para guardar todas as tabelas (DataFrames) de todos os bancos analisados
        todos_os_dados = []
        
        # Faz um loop para ler e processar cada arquivo listado na pasta
        for arquivo in arquivos:
            # Monta o caminho exato e completo do arquivo atual
            caminho = os.path.join(pasta_inputs, arquivo)
            print(f"🔄 Lendo: {arquivo}...")
            
            # Chama a função que processa o arquivo OFX e recebe de volta uma tabela contendo as informações dele
            df_resultado = ofx_to_dataframe(caminho)
            
            # Verifica se obtivemos um resultado válido e se a tabela de fato tem linhas (não é vazia)
            if df_resultado is not None and not df_resultado.empty:
                # Se sim, adiciona essa tabela na nossa lista que está guardando os dados de todos os arquivos
                todos_os_dados.append(df_resultado)
                # Exibe quantas transações foram extraídas do arquivo
                print(f"   ✔️ {len(df_resultado)} transações extraídas.")

        # Após varrer todos os arquivos, verifica se guardamos tabelas na nossa lista
        if todos_os_dados:
            print("\n📦 Consolidando todos os arquivos...")
            
            # O poder do Pandas: concatena (empilha verticalmente) todas as tabelas da lista, criando um único DataFrame gigante
            # O ignore_index=True garante que o Pandas vai gerar uma nova numeração sequencial para as linhas (0, 1, 2, 3...)
            df_consolidado = pd.concat(todos_os_dados, ignore_index=True)
            
            # Define o caminho final e o nome do arquivo CSV unificado
            caminho_saida = os.path.join(pasta_saida, "analise_consolidado_final.csv")
            
            # Exporta/salva o nosso "DataFrame gigante" em um arquivo CSV.
            # O 'sep=;' usa o ponto e vírgula para separar as colunas (ideal para o Excel brasileiro).
            # O 'index=False' diz para não exportar aquela numeração sequencial das linhas.
            # O 'encoding='utf-8-sig'' garante que palavras com acento ou cedilha sejam lidas corretamente pelo Excel no Windows.
            df_consolidado.to_csv(caminho_saida, sep=';', index=False, encoding='utf-8-sig')
            
            # Avisa o usuário que tudo deu certo, informando o total de registros (linhas) salvos
            print(f"✅ SUCESSO! Arquivo ÚNICO gerado com {len(df_consolidado)} transações no total.")
            # Indica a pasta exata onde o arquivo final foi depositado
            print(f"📂 Salvo em: {caminho_saida}")