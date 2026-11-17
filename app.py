import time
from modules.visual import *
from modules.funcional import *
from modules.stations import *
import streamlit as st
import pandas as pd

st.title("Bem-vindo(a) ao AquaVIS!")

st.markdown("Selecione uma das opções para acessar os dados de uma estação específica:")

st.session_state.title = st.text_input("Código da estação")

if st.button("Buscar Estação", type="secondary"):
    if st.session_state['title'] != '':
        with st.spinner("Abrindo estação...", show_time=True):
            csv, nome_estacao = extrair_dados(st.session_state.title)

            if "data" not in st.session_state:
                st.session_state.csv_data = None
                st.session_state["csv_data"] = csv
                criar_df()
    else:
        st.error("Digite o número da estação antes de clicar no botão!")

    
st.markdown("OU")

# Botão de upload de arquivos
if st.button("Upload de arquivo CSV", type="secondary"):
    arquivo = st.file_uploader( 
            "📄 Importar arquivo CSV/XLSX", 
            type=["csv", "xlsx"],
            accept_multiple_files=False,
            on_change=criar_df,
            key='csv_data'
            )
    
    

if "df" in st.session_state:
    codigo = str(st.session_state['df'].loc[0, "EstacaoCodigo"])
    _, _, nome_estacao = launch_navegador(codigo, download=False)
    nome_estacao = processa_texto(nome_estacao)
    st.session_state['codigo_estacao'] = codigo
    st.session_state['nome_estacao'] = nome_estacao

    st.success(f"Estação encontrada! - {codigo} / {nome_estacao}")
    st.divider()

    if st.button("Prosseguir para análise", type="primary"):
        st.switch_page("pages/analysis.py")