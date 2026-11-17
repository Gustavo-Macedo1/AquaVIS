from modules.visual import *
from modules.funcional import *
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title(":blue[AquaVIS]")
st.header(f"Estação {st.session_state['codigo_estacao']} - {st.session_state['nome_estacao']}")
st.subheader("Série completa", divider="blue")

if "df" in st.session_state:
    with st.sidebar:
        st.title(":blue[AquaVIS]")
        st.subheader("Análise de dados hidrológicos")
        entrada_data()

    df = st.session_state.df
    df = df[df["Data"].between(st.session_state.data_inicial, st.session_state.data_final)]

    st.subheader("Visualização gráfica da série selecionada")
    fig = criar_grafico(df, codigo=st.session_state['codigo_estacao'])
    st.plotly_chart(fig)

    st.divider()
    st.subheader("Insights e Análises")

    col1, col2, col3 = st.columns(3)
    col1.metric("Número de registros", len(df), border=True)
    col2.metric("Dados faltantes", len(df[df['Media'].isna()]), border=True)
    col3.metric("Valor médio da cota", round(df['Media'].mean(), 2), border=True)
    
    st.divider()
    if st.button("Iniciar detecção de anomalias", type="primary"):
        st.session_state['df_original'] = df.copy()
        st.switch_page("pages/stage1.py")

