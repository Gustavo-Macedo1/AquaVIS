import streamlit as st
import pandas as pd
import datetime

def criar_df(caminho = None):

    if "df" not in st.session_state:
        st.session_state.df = None

    if "csv_data" in st.session_state:
        arquivo = st.session_state.csv_data
        df = pd.read_csv(arquivo, encoding="ISO-8859-1", delimiter=",")
        st.session_state["df"] = df

def entrada_data():
    df = st.session_state.df
    min_date = df["Data"].min()
    max_date = df["Data"].max()

    d = st.date_input(
        "Selecione a janela de interesse:",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY",
    )
    
    if isinstance(d, tuple) and len(d) == 2:
        d0 = d[0].strftime("%Y-%m-%d")
        d1 = d[1].strftime("%Y-%m-%d")

        st.session_state["data_inicial"] = str(d0)
        st.session_state["data_final"] = str(d1)
    else:
        st.warning("Selecione um intervalo de datas válido.")

def entrada_modelo():
    st.session_state["modelo"] = st.selectbox(
        "Selecione o modelo de detecção de anomalias:",
        ("K-Means Scorer", "Auto Encoder"),
        index=None,
        placeholder="Selecione o modelo"
    )