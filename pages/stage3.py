from modules.visual import *
from modules.funcional import *
from modules.models import *
import streamlit as st

st.title(":blue[AquaVIS]")
st.header(f"Estação {st.session_state['codigo_estacao']} - {st.session_state['nome_estacao']}")

st.divider()

st.subheader("Finalização e Download")
st.write("Nesta última seção, realizamos a finalização do processo de transformação da série, fazendo um comparativo entre as séries original e modificada," \
        " além de mostrar as modificações realizadas durante todas as etapas do fluxo do AquaVIS.")
st.divider()

st.subheader("Comparativo das séries original e modificada", divider="blue")

if "serie_temporal" in st.session_state:
    coluna1, coluna2 = st.columns(2, border=True)

    with coluna1:
        st.subheader("Visualizar - Série original:")
        serie_original = st.session_state['df_original'].copy()
        serie_modificada = st.session_state['df_provisorio'].copy()

        fig = criar_grafico(serie_original, codigo=st.session_state['codigo_estacao'])
        st.plotly_chart(fig)

        st.subheader("Insights e Análises")

        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Número de registros", len(serie_original), border=True)
            col2.metric("Dados faltantes", len(serie_original[serie_original['Media'].isna()]), border=True)
            col3.metric("Valor médio da cota", round(serie_original['Media'].mean(), 2), border=True)

    with coluna2:
        st.subheader("Visualizar - Série modificada:")
        fig = criar_grafico(serie_modificada, color=True, codigo=st.session_state['codigo_estacao'])
        st.plotly_chart(fig)

        st.subheader("Insights e Análises")
        
        with st.container(border=True):
            col4, col5, col6 = st.columns(3)
            col4.metric("Número de registros", len(serie_modificada), border=True)
            col5.metric("Dados faltantes", len(serie_modificada[serie_modificada['Media'].isna()]), border=True)
            col6.metric("Valor médio da cota", round(serie_modificada['Media'].mean(), 2), border=True)

    st.subheader("Modificações realizadas", divider="blue")

    st.markdown("- Preenchimento de dados faltantes por **regressão linear**;")
    st.markdown(f"- Uso do modelo **{st.session_state['modelo']}** para identificar anomalias;")

    if 'derivada' in st.session_state:
        st.markdown(f"- **Refinamento** de identificação de anomalias por derivadas primeira e segunda;")

    if 'transf_normal_para_outlier' in st.session_state:
        st.markdown(f"- Transformação de **dados normais em anomalias**;")

    if 'transf_outlier_para_normal' in st.session_state:
        st.markdown(f"- Transformação de **anomalias em dados normais**;")
    
    metodos = []
    if 'uso_regressao' in st.session_state:
        metodos.append("**regressão linear**")
    if 'uso_interpolacao_polinomial' in st.session_state:
        metodos.append("**interpolação polinomial**")
    if 'uso_interpolacao_spline' in st.session_state:
        metodos.append("**interpolação por spline**")

    string = ", ".join(metodos)
    
    if len(string) != 0:
        st.markdown(f"- Métodos de correção aplicados: {string}.")
    else:
        st.markdown(f"- Métodos de correção aplicados: nenhum.")

    st.divider()

    csv = serie_modificada.to_csv().encode("utf-8")

    st.download_button(label="Realizar download da série atualizada",
                       data=csv,
                       file_name="nova_serie.csv",
                       mime="text/csv",
                       icon=":material/download:",
                       type='primary')