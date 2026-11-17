import openpyxl
import pyodbc
import pandas as pd
import os
import time
from zipfile import ZipFile
from pathlib import Path
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Função para processar o nome da estação vindo da HidroWEB
def processa_texto(texto):
    conectivos = ["A", "E", "O", "DE", "DO", "DOS", "DA", "DAS", "PARA"]
    partes = [(txt[0] + txt[1:].lower())  if txt not in conectivos else txt.lower() for txt in texto.split()]
    return " ".join(partes)

def launch_navegador(estacao, download=True):

    if estacao.isnumeric():
        input_path = '//*[@id="mat-input-0"]'

    # Criando serviço para identificar versão do Chrome instalada
    servico = Service(ChromeDriverManager().install())

    # Definindo configuração para ocultar o navegador
    opcoes_chrome = webdriver.ChromeOptions()
    opcoes_chrome.add_argument("--headless")

    # Criando o navegador com as opções e a versão correta do driver
    navegador = webdriver.Chrome(service=servico, options=opcoes_chrome)


    # Utilizando Selenium para baixar o arquivo MDB de acordo com as chaves de pesquisa

    navegador.get("https://www.snirh.gov.br/hidroweb/serieshistoricas")
    navegador.find_element('xpath','//*[@id="mat-select-0"]/div/div[2]/div').click()
    navegador.find_element('xpath', '//*[@id="mat-option-2"]/span').click()
    navegador.find_element('xpath', input_path).send_keys(estacao)
    navegador.find_element('xpath', '/html/body/app-root/mat-sidenav-container/mat-sidenav-content/ng-component/form/ana-card/mat-card/mat-card-content/mat-card-actions/div/div/button[1]/span').click()

    # Aguarda operação do Selenium para baixar arquivo MDB
    time.sleep(3)
    input_code = navegador.find_element('xpath', '//*[@id="mat-tab-content-0-0"]/div/ana-card/mat-card/mat-card-content/ana-dados-convencionais-list/div/div[1]/table/tbody/tr[1]/td[2]').text
    station_name = navegador.find_element('xpath', '//*[@id="mat-tab-content-0-0"]/div/ana-card/mat-card/mat-card-content/ana-dados-convencionais-list/div/div[1]/table/tbody/tr/td[3]').text
    
    if download:
        navegador.find_element('xpath', '//*[@id="mat-tab-content-0-0"]/div/ana-card/mat-card/mat-card-content/ana-dados-convencionais-list/div/div[1]/table/tbody/tr/td[7]/button/span/mat-icon').click()
        time.sleep(5)

    return [navegador, input_code, station_name]

def get_default_download_directory():
    if os.name == 'nt':  # Windows
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    elif os.name == 'posix':  # macOS ou Linux
        return os.path.join(Path.home(), 'Downloads')
    else:
        raise NotImplementedError("Sistema operacional não suportado.")


def extracao_custom(codigo):
    # Obter o diretório padrão de downloads
    download_dir = get_default_download_directory()

    data_modificacao = lambda f: f.stat().st_mtime


    diretorio = Path(download_dir)
    arquivos = diretorio.glob(f'Estacao_{codigo}_MDB_*.zip')
    sorted_arquivos = sorted(arquivos, key=data_modificacao, reverse=True)
    nome_zip = sorted_arquivos[0].name

    # Extração do arquivo ZIP, seleção contendo o CSV de interesse


    zip = ZipFile(f"{download_dir}/{nome_zip}", 'r')
    nome_cotas = [arq for arq in zip.namelist() if arq.endswith('.mdb')][0] # Seleciona arquivo que termina com "Cotas.csv" dentro do ZIP

    zip.extract(nome_cotas, path="./data/mdb") # Extrai o arquivo de cotas

def obter_csv(codigo):
    # Caminho do arquivo MDB
    mdb_path = fr"./data/mdb/{codigo}.mdb"
    # Query SQL (consulta união)
    sql_query = """
    SELECT C.EstacaoCodigo, C.Data+0  AS Data, C.Cota01 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+0, C.Cota01, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+1  AS Data, C.Cota02 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+1, C.Cota02, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+2  AS Data, C.Cota03 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+2, C.Cota03, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+3  AS Data, C.Cota04 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+3, C.Cota04, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+4  AS Data, C.Cota05 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+4, C.Cota05, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+5  AS Data, C.Cota06 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+5, C.Cota06, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+6  AS Data, C.Cota07 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+6, C.Cota07, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+7  AS Data, C.Cota08 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+7, C.Cota08, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+8  AS Data, C.Cota09 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+8, C.Cota09, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+9  AS Data, C.Cota10 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+9, C.Cota10, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+10  AS Data, C.Cota11 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+10, C.Cota11, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+11  AS Data, C.Cota12 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+11, C.Cota12, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+12  AS Data, C.Cota13 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+12, C.Cota13, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+13  AS Data, C.Cota14 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+13, C.Cota14, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+14  AS Data, C.Cota15 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+14, C.Cota15, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+15  AS Data, C.Cota16 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+15, C.Cota16, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+16  AS Data, C.Cota17 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+16, C.Cota17, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+17  AS Data, C.Cota18 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+17, C.Cota18, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+18  AS Data, C.Cota19 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+18, C.Cota19, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+19  AS Data, C.Cota20 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+19, C.Cota20, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+20  AS Data, C.Cota21 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+20, C.Cota21, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+21  AS Data, C.Cota22 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+21, C.Cota22, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+22  AS Data, C.Cota23 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+22, C.Cota23, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+23  AS Data, C.Cota24 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+23, C.Cota24, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+24  AS Data, C.Cota25 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+24, C.Cota25, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+25  AS Data, C.Cota26 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+25, C.Cota26, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+26  AS Data, C.Cota27 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+26, C.Cota27, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+27  AS Data, C.Cota28 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+27, C.Cota28, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+28  AS Data, C.Cota29 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+28, C.Cota29, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION 
    SELECT C.EstacaoCodigo, C.Data+29  AS Data, C.Cota30 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+29, C.Cota30, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=1) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0) UNION SELECT C.EstacaoCodigo, C.Data+30  AS Data, C.Cota31 AS Media FROM Cotas As C GROUP BY C.EstacaoCodigo, C.Data+30, C.Cota31, C.MediaDiaria, C.NivelConsistencia, C.Importado, C.Temporario, C.Removido  HAVING (C.MediaDiaria=1) AND (C.NivelConsistencia=2) AND (C.Importado=0) AND (C.Temporario=0) AND (C.Removido=0);
    """

    # Conexão com o arquivo MDB
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={mdb_path};"
    )
    try:
        # Conectar ao banco de dados
        conn = pyodbc.connect(conn_str)
        print("Conexão bem-sucedida com o arquivo MDB.")
        
        # Executar a consulta e carregar os resultados em um DataFrame
        df = pd.read_sql(sql_query, conn)
        print("Consulta executada com sucesso.")
        
        # Fechar a conexão
        conn.close()

        # Salvar os dados como XLSX
        output_path = fr"./data/csv/cotas_{codigo}.csv"
        df.to_csv(output_path, index=False)
        print(f"Dados salvos em {output_path}")

    except Exception as e:
        print(f"Erro: {e}")

def extrair_dados(input, download=True):
    _, codigo, nome_estacao = launch_navegador(input, download)
    extracao_custom(codigo)
    obter_csv(codigo)

    return (f"./data/csv/cotas_{codigo}.csv", nome_estacao)
    