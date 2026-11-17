import streamlit as st
import torch
import pickle
import statistics
import numpy
from modules.funcional import *
from modules.models import *

st.title(":blue[AquaVIS]")
st.header(f"Estação {st.session_state['codigo_estacao']} - {st.session_state['nome_estacao']}")
st.subheader("Detecção de Anomalias", divider="blue")

with st.sidebar:
    st.title(":blue[AquaVIS]")
    st.subheader("Análise de dados hidrológicos")
    entrada_data()

if "df" in st.session_state:
    device = torch.device("cpu")
    df = st.session_state.df
    df = df[df["Data"].between(st.session_state.data_inicial, st.session_state.data_final)]
    ae_scorer = joblib.load("models/auto_encoder_scorer.pkl")
    kmeans_scorer = joblib.load("models/kmeans_scorer.pkl")
    serie_temporal = preparar_serie(df)
    


    st.subheader("Etapa 1: Detecção de outliers")
    st.write("A detecção de outliers é um passo importante no pré-processamento de dados. "
             "Outliers podem distorcer a análise e levar a conclusões incorretas. "
             "Neste caso, a detecção de outliers é realizada para garantir que os dados sejam representativos e confiáveis.")
    st.markdown("**Selecione abaixo as configurações do sistema de detecção de outliers:**")

    st.divider()

    modelo = st.radio(
        "Selecione o modelo para detectar outliers:",
        ["K-Means Scorer", "Auto Encoder"],
        index=None,
    )

    quantil = st.slider("Selecione o valor do quantil do detector de anomalias",
                         0.0,
                         1.0, 
                         0.85,
                         help="Quanto mais alto o valor do quantil, mais rigoroso será o detector de anomalias. "
                              "Valores mais baixos resultarão em mais anomalias detectadas.",)
    
    detector = QuantileDetector(high_quantile=quantil)
    
    st.divider()

    # Preparação dos resultados
    serie_outliers1, serie_temporal1 = prepara_resultados(kmeans_scorer, detector, serie_temporal)
    serie_outliers2, serie_temporal2 = prepara_resultados(ae_scorer, detector, serie_temporal)

    serie_outliers1 = completar_data(serie_temporal1, serie_outliers1)
    serie_outliers2 = completar_data(serie_temporal2, serie_outliers2)

    # Refinamento por derivada

    # Cálculo da derivada da série obtida
    derivada = serie_temporal1.copy()
    derivada['Derivada 1'] = serie_temporal1['Media'].diff()
    derivada['Derivada 1'] = derivada['Derivada 1'].fillna(0)

    # Cálculo da derivada segunda
    derivada['Derivada 2'] = derivada['Derivada 1'].diff()
    derivada['Derivada 2'] = derivada['Derivada 2'].fillna(0)

    # Cálculo da média e do desvio padrão da derivada
    media_derivada = derivada['Derivada 1'].mean()
    desvio_derivada = derivada['Derivada 1'].std()
    maximo_derivada = derivada['Derivada 1'].max()
    minimo_derivada = derivada['Derivada 1'].min()

    der_ref = False

    if st.checkbox("Usar refinamento por derivada",
                    help="O refinamento por derivada combina a predição do modelo às derivadas primeira e segunda para aumentar a confiabilidade" \
                    "da detecção de anomalias. Dessa forma, o refinamento acusa apenas anomalias com maiores chances de serem anomalias reais."):
        der_ref = True
        derivada['Media'] = derivada['Media'] + 5 * derivada['Derivada 1']
        serie_temporal_derivada = preparar_serie(derivada)

        serie_outliers3, serie_temporal3 = prepara_resultados(kmeans_scorer, detector, serie_temporal_derivada)
        serie_outliers4, serie_temporal4 = prepara_resultados(ae_scorer, detector, serie_temporal_derivada)

        serie_outliers3 = completar_data(serie_temporal3, serie_outliers3)
        serie_outliers4 = completar_data(serie_temporal4, serie_outliers4)

        serie_temporal3['Media'] = serie_temporal1['Media']
        holder1 = (serie_temporal1[serie_temporal1['Data'].between(serie_outliers3.loc[0, 'Data'], serie_outliers3.loc[len(serie_outliers3) - 1, 'Data'])])
        holder1.reset_index(inplace=True)
        serie_outliers3['Media'] = holder1['Media']
        serie_outliers3['Derivada'] = serie_outliers3['Media'].diff()
        serie_outliers3['Derivada'] = serie_outliers3['Derivada'].fillna(0)
        serie_outliers3['Derivada Seg'] = serie_outliers3['Derivada'].diff()
        serie_outliers3['Derivada Seg'] = serie_outliers3['Derivada Seg'].fillna(0)
        serie_outliers3['Media'].loc[serie_outliers3['Outlier_pontuador'] == 0.0] = None

        serie_temporal4['Media'] = serie_temporal2['Media']
        holder2 = (serie_temporal2[serie_temporal2['Data'].between(serie_outliers4.loc[0, 'Data'], serie_outliers4.loc[len(serie_outliers4) - 1, 'Data'])])
        holder2.reset_index(inplace=True)
        serie_outliers4['Media'] = holder2['Media']
        serie_outliers4['Derivada'] = serie_outliers4['Media'].diff()
        serie_outliers4['Derivada'] = serie_outliers4['Derivada'].fillna(0)
        serie_outliers4['Derivada Seg'] = serie_outliers4['Derivada'].diff()
        serie_outliers4['Derivada Seg'] = serie_outliers4['Derivada Seg'].fillna(0)
        serie_outliers4['Media'].loc[serie_outliers4['Outlier_pontuador'] == 0.0] = None

        media_d2_janelas = []
        d2_atual = []
        janelas_datas = []
        tamanho_d2_atual = 0
        
        for _, linha in serie_outliers3.iterrows():
            if not numpy.isnan(linha['Media']):
                d2_atual.append(abs(linha['Derivada Seg']))
                tamanho_d2_atual += 1

                if tamanho_d2_atual == 1:
                    data_inicial = linha['Data']
            else:
                if tamanho_d2_atual > 0:
                    data_final = linha['Data']
                    media_d2 = statistics.fmean(d2_atual)
                    media_d2_janelas.append(media_d2)
                    janelas_datas.append((data_inicial, data_final))
                    d2_atual = []
                    tamanho_d2_atual = 0

        desvio_d2_janelas = (pd.Series(media_d2_janelas)).std()
        janelas_normais = []
        i = 0

        for media in media_d2_janelas:
            if media <= 0.8 * desvio_d2_janelas:
                janelas_normais.append(janelas_datas[i])
            i += 1

        for data_inicial, data_final in janelas_normais:
            mask = (serie_outliers3['Data'].between(data_inicial, data_final))
            serie_outliers3.loc[mask, 'Media'] = None
            serie_outliers3.loc[mask, 'Outlier_pontuador'] = 0

        # ===========
        
        media_d2_janelas = []
        d2_atual = []
        janelas_datas = []
        tamanho_d2_atual = 0

        for _, linha in serie_outliers4.iterrows():
            if not numpy.isnan(linha['Media']):
                d2_atual.append(abs(linha['Derivada Seg']))
                tamanho_d2_atual += 1

                if tamanho_d2_atual == 1:
                    data_inicial = linha['Data']
            else:
                if tamanho_d2_atual > 0:
                    data_final = linha['Data']
                    media_d2 = statistics.fmean(d2_atual)
                    media_d2_janelas.append(media_d2)
                    janelas_datas.append((data_inicial, data_final))
                    d2_atual = []
                    tamanho_d2_atual = 0

        desvio_d2_janelas = (pd.Series(media_d2_janelas)).std()
        janelas_normais = []
        i = 0

        for media in media_d2_janelas:
            if media <= 0.8 * desvio_d2_janelas:
                janelas_normais.append(janelas_datas[i])
            i += 1

        for data_inicial, data_final in janelas_normais:
            mask = (serie_outliers4['Data'].between(data_inicial, data_final))
            serie_outliers4.loc[mask, 'Media'] = None
            serie_outliers4.loc[mask, 'Outlier_pontuador'] = 0

        # Preparação do plot dos resultados
        fig_kmeans, relatorio_kmeans = relatorio_anomalias(serie_outliers3, serie_temporal3, "K-Means Scorer")
        fig_ae, relatorio_ae = relatorio_anomalias(serie_outliers4, serie_temporal4, "Auto Encoder")

        # Registro da opção de refinamento por derivada (relatório final)
        st.session_state['derivada'] = True
    else:
        # Preparação do plot dos resultados
        fig_kmeans, relatorio_kmeans = relatorio_anomalias(serie_outliers1, serie_temporal1, "K-Means Scorer")
        fig_ae, relatorio_ae = relatorio_anomalias(serie_outliers2, serie_temporal2, "Auto Encoder")

    if modelo:
        if modelo == "K-Means Scorer":
            relatorio = relatorio_kmeans
            delta1, delta2, delta3 = str(relatorio_kmeans[0] - relatorio_ae[0]), str(relatorio_kmeans[1] - relatorio_ae[1]), str(round(relatorio_kmeans[2] - relatorio_ae[2], 2))
            fig = fig_kmeans
            st.plotly_chart(fig)
        else:
            relatorio = relatorio_ae
            delta1, delta2, delta3 = str(relatorio_ae[0] - relatorio_kmeans[0]), str(relatorio_ae[1] - relatorio_kmeans[1]), str(round(relatorio_ae[2] - relatorio_kmeans[2], 2))
            fig = fig_ae
            st.plotly_chart(fig)
            
        col1, col2, col3 = st.columns(3)
        col1.metric("Outliers", relatorio[0], delta=delta1, border=True, help="As setas de comparação (em vermelho ou verde) comparam a quantidade de anomalias entre os dois modelos.")
        col2.metric("Outliers extremos", relatorio[1], delta=delta2, border=True, help="As setas de comparação (em vermelho ou verde) comparam a quantidade de anomalias extremas entre os dois modelos.")
        col3.metric("Desvio padrão dos outliers", relatorio[2], delta=delta3, border=True, help="As setas de comparação (em vermelho ou verde) comparam o valor do desvio padrão entre os dois modelos.")

        st.divider()

        if st.button("Confirmar modelo e prosseguir para Correção de Anomalias", type="primary"):
            if modelo == "K-Means Scorer":
                if der_ref == False:
                    st.session_state['serie_outliers'] = serie_outliers1
                    st.session_state['serie_temporal'] = serie_temporal1
                else:
                    st.session_state['serie_outliers'] = serie_outliers3
                    st.session_state['serie_temporal'] = serie_temporal3

                st.session_state['modelo'] = modelo
            else:   
                if der_ref == False:
                    st.session_state['serie_outliers'] = serie_outliers2
                    st.session_state['serie_temporal'] = serie_temporal2
                else:
                    st.session_state['serie_outliers'] = serie_outliers4
                    st.session_state['serie_temporal'] = serie_temporal4
                
                st.session_state['modelo'] = modelo

            st.session_state['janela'] = 0
            st.session_state['df_provisorio'] = st.session_state['serie_temporal'].copy()
            st.session_state['df_provisorio']["Data"] = pd.to_datetime(st.session_state['df_provisorio']["Data"], format="%Y-%m-%d")
            st.session_state['placeholder'] = 0
            st.session_state['order_placeholder'] = 0
            st.switch_page("pages/stage2.py")
    else:
        st.warning("Atenção: nenhum modelo foi selecionado.")
