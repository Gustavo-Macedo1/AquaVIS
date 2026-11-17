from modules.visual import *
from modules.funcional import *
from modules.models import *
import streamlit as st
import pandas as pd
import time

def resetar_janela():
    st.session_state['janela'] = 0
    
def resetar_ordem():
    ordem = 2

transf_normal_para_outlier = False
transf_outlier_para_normal = False

# st.set_page_config(layout="wide")

st.title(":blue[AquaVIS]")
st.header(f"Estação {st.session_state['codigo_estacao']} - {st.session_state['nome_estacao']}")
st.subheader("Detecção de Anomalias", divider="blue")

with st.sidebar:
    st.title(":blue[AquaVIS]")
    st.subheader("Análise de dados hidrológicos")
    entrada_data()

if "serie_temporal" in st.session_state:
    # Definição de variáveis iniciais
    provisorio = st.session_state['df_provisorio'].copy()
    outliers = st.session_state['serie_outliers'].copy()
    modelo = st.session_state.modelo
    df = provisorio.copy()
    df = df[df["Data"].between(st.session_state.data_inicial, st.session_state.data_final)]

    if 'datas_modificadas' in st.session_state:
        pass
    else:
        st.session_state['datas_modificadas'] = []

    if 'datas_modificadas2' in st.session_state:
        pass
    else:
        st.session_state['datas_modificadas2'] = []

    # Textos iniciais da página
    st.subheader("Etapa 2: Correção da série")
    st.write("No contexto do AquaVIS, a interpolação e a regressão são métodos utilizados para preencher dados ausentes em uma série temporal. "
             "Neste caso, os dados classificados como outliers serão deletados, sendo posteriormente preenchidos por algum método de interpolação ou  regressão. " \
             "A correção é aplicada para garantir que a série temporal esteja completa e pronta para análise.")
    st.markdown("Para iniciar a correção, selecione a periodicidade das correções através de uma das opções abaixo:")

    # Set-up de dataframes e períodos
    df_atual = df.copy()
    df_atual["Data"] = pd.to_datetime(df_atual["Data"], format="%Y-%m-%d")

    meses = tuple(["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    anos = tuple(df_atual["Data"].dt.year.unique())

    disabled = False


    # Colunas de cima
    c1, c2, c3 = st.columns(3, border=True)

    # Seleção manual
    with c1: 
        st.markdown("**Periodicidade personalizada**")
        manual = st.checkbox("Selecionar intervalos manualmente", value=False, key="manual_selection")

        if manual:
            min_date = df_atual["Data"].min()
            max_date = df_atual["Data"].max()

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

                data_inicial = str(d0)
                data_final = str(d1)
            else:
                st.warning("Selecione um intervalo de datas válido.")

            df_atual = df_atual[df_atual['Data'].between(data_inicial, data_final)]
            df_atual.reset_index(inplace=True)
            outliers_atual = outliers[outliers['Data'].between(data_inicial, data_final)]
            outliers_atual.reset_index(inplace=True)

    # Periodicidade fixa
    with c2:
        st.markdown("**Periodicidade fixa**")

        if manual:
            disabled = True
        else:
            disabled = False

        periodicidade = st.radio(
            "Selecione uma das periodicidades de correção:",
            ["Mês a mês", "Ano a ano"],
            index=0,
            disabled=disabled,
            on_change=resetar_janela
        )

        if periodicidade == "Mês a mês":
            intervalos_outliers = []

            for ano_ in anos:
                for mes_ in range(1, 13):
                    if outliers[(outliers["Data"].dt.month == mes_) & (outliers["Data"].dt.year == ano_)]['Media'].any() == True:
                        intervalos_outliers.append((mes_, ano_))
            

            if not manual:
                st.write("Você selecionou a periodicidade mês a mês. ")
                janela = st.session_state['janela']
                
                if (len(intervalos_outliers) > 0):
                    mes, ano = intervalos_outliers[janela]

                    df_atual = df_atual[(df_atual["Data"].dt.month == mes) & (df_atual["Data"].dt.year == ano)]
                    df_atual.reset_index(inplace=True)
                    outliers_atual = outliers[(outliers["Data"].dt.month == mes) & (outliers["Data"].dt.year == ano)]
                    outliers_atual.reset_index(inplace=True)
                    df_plot = df[df["Data"].between(df_atual['Data'].loc[0], df_atual['Data'].loc[len(df_atual) - 1])]

                    data_inicial = df_atual.loc[0, 'Data']
                    data_final = df_atual.loc[len(df_atual) - 1, 'Data']
                
                    st.markdown(f"**Mês a corrigir: {mes}/{ano}.**")


                    bc1, bc2, bc3 = st.columns(3)

                    with bc1:
                        if st.button("Voltar janela", type="primary"):
                            st.session_state['janela'] -= 1

                            if st.session_state['janela'] < 0:
                                st.session_state['janela'] = len(intervalos_outliers) - 1
                                st.rerun()
                            else:
                                st.rerun()

                    with bc2:
                        if st.button("Avançar janela", type="primary"):
                            st.session_state['janela'] += 1

                            if st.session_state['janela'] >= len(intervalos_outliers):
                                st.session_state['janela'] = 0
                                st.rerun()
                            else:
                                st.rerun()
                    
                    with bc3:
                        if st.button("Resetar índice", type="secondary"):
                            provisorio = None
                            st.session_state['janela'] = 0
                            st.rerun()

        elif periodicidade == 'Ano a ano':
            intervalos_outliers = []

            for ano_ in anos:
                if outliers[outliers["Data"].dt.year == ano_]['Media'].any() == True:
                        intervalos_outliers.append((ano_))

            if not manual:
                st.write("Você selecionou a periodicidade ano a ano. ")
                janela = st.session_state['janela']
                
                if len(intervalos_outliers) > 0:
                    ano = intervalos_outliers[janela]

                    df_atual = df_atual[df_atual["Data"].dt.year == ano]
                    df_atual.reset_index(inplace=True)
                    outliers_atual = outliers[outliers["Data"].dt.year == ano]
                    outliers_atual.reset_index(inplace=True)
                    df_plot = df[df["Data"].between(df_atual['Data'].loc[0], df_atual['Data'].loc[len(df_atual) - 1])]

                    data_inicial = df_atual.loc[0, 'Data']
                    data_final = df_atual.loc[len(df_atual) - 1, 'Data']
                
                    st.markdown(f"**Ano a corrigir: {ano}.**")

                    bc3, bc4, bc5 = st.columns(3)

                    with bc3:
                        if st.button("Voltar janela", type="primary"):
                            st.session_state['janela'] -= 1

                            if st.session_state['janela'] < 0:
                                st.session_state['janela'] = len(intervalos_outliers) - 1
                                st.rerun()
                            else:
                                st.rerun()

                    with bc4:
                        if st.button("Avançar janela", type="primary"):
                            st.session_state['janela'] += 1

                            if st.session_state['janela'] >= len(intervalos_outliers):
                                st.session_state['janela'] = 0
                                st.rerun()
                            else:
                                st.rerun()
                    
                    with bc5:
                        if st.button("Resetar índice", type="secondary"):
                            provisorio = None
                            st.session_state['janela'] = 0
                            st.rerun()





    # Método de correção
    if (len(intervalos_outliers) > 0):

        with c3:
            st.markdown("**Método de correção de anomalias**")
            metodo = st.radio(
                "Selecione o método de correção para visualizar:",
                ["Regressão linear", "Interpolação polinomial", "Interpolação por spline"],
                index=st.session_state['placeholder'],
                on_change=resetar_ordem,
            )

            if metodo == "Regressão linear":
                st.write("Você selecionou o método de regressão linear. ")
                
                df_atual_corrigido = df_atual.copy()    
                outliers_atual_corrigido = outliers_atual.copy()
                df_atual_corrigido['Outlier_pontuador'] = 0

                datas = outliers_atual_corrigido[outliers_atual_corrigido['Outlier_pontuador'] == 1.0]['Data'].dt.strftime('%Y-%m-%d').tolist()

                for data in datas:
                    df_atual_corrigido.loc[df_atual_corrigido['Data'] == data, 'Outlier_pontuador'] = 1.0

                new_trace = df_atual_corrigido.copy()
                new_trace['Media'] = None
                

                # Verifica se a série foi transformada
                if 'datas_para_transformar' in st.session_state:
                    if len(st.session_state['datas_para_transformar']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar'])
                        
                        # indexes.loc[mask, 'Media'] = None
                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Media'] = None 

                        transf_outlier_para_normal = True
                
                if 'datas_para_transformar2' in st.session_state:
                    if len(st.session_state['datas_para_transformar2']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar2'])
                        # mask_df = df_atual_corrigido['Data'].isin(st.session_state['datas_para_transformar2'])
                        
                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Media'] = df_atual_corrigido.loc[mask, 'Media']

                        transf_normal_para_outlier = True

                # Lista de índices de df_atual_corrigido que são anomalias
                indexes = df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'].index.tolist()
                
                # Se o primeiro valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[0] == 1.0:
                    st.warning("Atenção: o primeiro valor da série é um outlier. ")
                    df_atual_corrigido.loc[0, 'Outlier_pontuador'] = 0.0
                    indexes.insert(0, 0)

                # Se o último valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[len(df_atual_corrigido) - 1] == 1.0:
                    st.warning("Atenção: o último valor da série é um outlier. ")
                    df_atual_corrigido.loc[len(df_atual_corrigido) - 1, 'Outlier_pontuador'] = 0.0
                    indexes.append(len(df_atual_corrigido) - 1)

                # Apaga os outliers da série para aplicar a regressão
                df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'] = None
                df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Outlier_pontuador'] = 0

                # Aplica a regressão linear
                prov_indexes = list(provisorio[provisorio['Data'].between(data_inicial, data_final)].index)
                provisorio.loc[prov_indexes, "Media"] = df_atual_corrigido["Media"].values
                provisorio.interpolate(method='linear', inplace=True)
                df_atual_corrigido.interpolate(method='linear', inplace=True)

                # Criação do traço de correção
                new_trace['Media'].loc[indexes] = df_atual_corrigido.loc[indexes, 'Media']
                new_trace = new_trace['Media']

                # Placeholder para segurar a seleção da correção
                st.session_state['placeholder'] = 0

            elif metodo == "Interpolação polinomial":
                st.write("Você selecionou o método de interpolação polinomial. ")

                ordem = st.number_input("Insira a ordem do polinômio:", min_value=2, max_value=10)
                
                df_atual_corrigido = df_atual.copy()    
                outliers_atual_corrigido = outliers_atual.copy()
                df_atual_corrigido['Outlier_pontuador'] = 0

                datas = outliers_atual_corrigido[outliers_atual_corrigido['Outlier_pontuador'] == 1.0]['Data'].dt.strftime('%Y-%m-%d').tolist()

                for data in datas:
                    df_atual_corrigido.loc[df_atual_corrigido['Data'] == data, 'Outlier_pontuador'] = 1.0

                new_trace = df_atual_corrigido.copy()
                new_trace['Media'] = None
                

                # Verifica se a série foi transformada
                if 'datas_para_transformar' in st.session_state:
                    if len(st.session_state['datas_para_transformar']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar'])
                        
                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Media'] = None 
                        transf_outlier_para_normal = True
                
                if 'datas_para_transformar2' in st.session_state:
                    if len(st.session_state['datas_para_transformar2']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar2'])
                        
                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 1
                        df_atual.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Media'] = df_atual_corrigido.loc[mask, 'Media']
                        outliers_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual_corrigido.loc[mask, 'Media'] = df_atual_corrigido.loc[mask, 'Media']

                        transf_normal_para_outlier = True

                # Lista de índices de df_atual_corrigido que são anomalias
                indexes = df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'].index.tolist()
                
                # Se o primeiro valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[0] == 1.0:
                    st.warning("Atenção: o primeiro valor da série é um outlier. ")
                    df_atual_corrigido.loc[0, 'Outlier_pontuador'] = 0.0
                    indexes.insert(0, 0)

                # Se o último valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[len(df_atual_corrigido) - 1] == 1.0:
                    st.warning("Atenção: o último valor da série é um outlier. ")
                    df_atual_corrigido.loc[len(df_atual_corrigido) - 1, 'Outlier_pontuador'] = 0.0
                    indexes.append(len(df_atual_corrigido) - 1)

                num_outliers = len(outliers_atual.loc[(outliers_atual['Outlier_pontuador'] > 0), 'Outlier_pontuador'].values)

                if (len(outliers_atual) - num_outliers) < (ordem + 1):
                    st.error(f"ERRO: Para a interpolação de grau {ordem}, é necessário haver {ordem + 1} pontos normais! Atualmente existem {(len(outliers_atual) - num_outliers)}.")
                else:
                    # Apaga os outliers da série para aplicar a regressão
                    df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'] = None
                    df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Outlier_pontuador'] = 0

                    # Aplica a interpolação
                    prov_indexes = provisorio[provisorio['Data'].between(data_inicial, data_final)].index
                    provisorio.loc[prov_indexes, "Media"] = df_atual_corrigido["Media"].values
                    provisorio['Media'].interpolate(method='polynomial', order=ordem, inplace=True)
                    df_atual_corrigido['Media'].interpolate(method='polynomial', order=ordem, inplace=True)

                    # Criação do traço de correção
                    new_trace['Media'].loc[indexes] = df_atual_corrigido.loc[indexes, 'Media']
                    new_trace = new_trace['Media']

                    # Placeholder para segurar a seleção da correção
                    st.session_state['placeholder'] = 1
                
            elif metodo == "Interpolação por spline":
                st.write("Você selecionou o método de interpolação por spline. ")

                ordem = st.number_input("Insira a ordem do polinômio:", min_value=2, max_value=5)
                
                df_atual_corrigido = df_atual.copy()    
                outliers_atual_corrigido = outliers_atual.copy()
                df_atual_corrigido['Outlier_pontuador'] = 0

                datas = outliers_atual_corrigido[outliers_atual_corrigido['Outlier_pontuador'] == 1.0]['Data'].dt.strftime('%Y-%m-%d').tolist()

                for data in datas:
                    df_atual_corrigido.loc[df_atual_corrigido['Data'] == data, 'Outlier_pontuador'] = 1.0

                new_trace = df_atual_corrigido.copy()
                new_trace['Media'] = None
                

                # Verifica se a série foi transformada
                if 'datas_para_transformar' in st.session_state:
                    if len(st.session_state['datas_para_transformar']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar'])

                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 0
                        outliers_atual.loc[mask, 'Media'] = None 

                        transf_outlier_para_normal = True
                
                if 'datas_para_transformar2' in st.session_state:
                    if len(st.session_state['datas_para_transformar2']) > 0:
                        mask = outliers_atual['Data'].isin(st.session_state['datas_para_transformar2'])
                        
                        df_atual_corrigido.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Outlier_pontuador'] = 1
                        outliers_atual.loc[mask, 'Media'] = df_atual_corrigido.loc[mask, 'Media']

                        transf_normal_para_outlier = True

                # Lista de índices de df_atual_corrigido que são anomalias
                indexes = df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'].index.tolist()
                
                # Se o primeiro valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[0] == 1.0:
                    st.warning("Atenção: o primeiro valor da série é um outlier. ")
                    df_atual_corrigido.loc[0, 'Outlier_pontuador'] = 0.0
                    indexes.insert(0, 0)

                # Se o último valor da série for um outlier, exibe um aviso e corrige o valor para não estourar a interpolação
                if df_atual_corrigido['Outlier_pontuador'].loc[len(df_atual_corrigido) - 1] == 1.0:
                    st.warning("Atenção: o último valor da série é um outlier. ")
                    df_atual_corrigido.loc[len(df_atual_corrigido) - 1, 'Outlier_pontuador'] = 0.0
                    indexes.append(len(df_atual_corrigido) - 1)

                num_outliers = len(outliers_atual.loc[(outliers_atual['Outlier_pontuador'] > 0), 'Outlier_pontuador'].values)

                if (len(outliers_atual) - num_outliers) < (ordem + 1):
                    st.error(f"ERRO: Para a interpolação de grau {ordem}, é necessário haver {ordem + 1} pontos normais! Atualmente existem {(len(outliers_atual) - num_outliers)}.")
                else:
                    # Apaga os outliers da série para aplicar a regressão
                    df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Media'] = None
                    df_atual_corrigido.loc[df_atual_corrigido['Outlier_pontuador'] != 0.0, 'Outlier_pontuador'] = 0

                    # Aplica a interpolação por spline
                    prov_indexes = provisorio[provisorio['Data'].between(data_inicial, data_final)].index
                    provisorio.loc[prov_indexes, "Media"] = df_atual_corrigido["Media"].values
                    provisorio['Media'].interpolate(method='spline', order=ordem, inplace=True)
                    df_atual_corrigido['Media'].interpolate(method='spline', order=ordem, inplace=True)

                    # Criação do traço de correção
                    new_trace['Media'].loc[indexes] = df_atual_corrigido.loc[indexes, 'Media']
                    new_trace = new_trace['Media']

                    # Placeholder para segurar a seleção da correção
                    st.session_state['placeholder'] = 2
            else:
                st.warning("Atenção: nenhum método de correção foi selecionado.")
        
        # =========== Transformação da série ===============

        st.subheader("Transformação personalizada da série")
        col_transformacao1, col_transformacao2 = st.columns(2, border=True)

        with col_transformacao1:

            with st.container(border=True):
                st.subheader("Transformar anomalias em dados normais")

                datas_outliers = (outliers_atual.loc[(outliers_atual['Outlier_pontuador'] != 0), 'Data'])
                datas_outliers = datas_outliers.dt.normalize()
                inicio_janela = outliers_atual.loc[0, 'Data']
                final_janela = outliers_atual.loc[len(outliers_atual) - 1, 'Data']

                # =========================================

                d = st.date_input(
                    "Insira o intervalo a ser modificado",
                    (inicio_janela, final_janela),
                    min_value=inicio_janela,
                    max_value=final_janela,
                    format="DD/MM/YYYY",
                )
                
                datas = [pd.to_datetime(data).normalize() for data in d]
                datas = outliers_atual.loc[outliers_atual['Data'].between(datas[0], datas[1]), 'Data']

                for data in datas:
                    if data.date() in datas_outliers.dt.date.values:
                        media = outliers_atual.loc[(outliers_atual['Data'] == data), 'Media'].values[0]
                        bloquear_add = False
                    else:
                        st.error("Existem pontos normais no intervalo.")
                        bloquear_add = True
                        break
                
                subcol1, subcol2, subcol3 = st.columns([1,2,1])

                with subcol1:
                    adicionou = False
                    if st.button("Adicionar datas na lista", disabled=bloquear_add):
                        for data in datas:
                            if data not in st.session_state['datas_modificadas']:
                                st.session_state['datas_modificadas'].append(data)
                        adicionou = True

                if adicionou == True:
                    st.success(f"Datas adicionadas na lista com sucesso!")

                with subcol2:
                    with st.popover("Mostrar lista de datas atual"):
                        i = 1
                        for data_ in st.session_state['datas_modificadas']:
                            st.write(f"Data nº {i}: {data_}")
                            i += 1
                
                if len(st.session_state['datas_modificadas']) > 0:
                    disabled_transformacao = False
                else:
                    disabled_transformacao = True
                
                if st.button("Aplicar transformação", type="primary", disabled=disabled_transformacao):
                    if transf_normal_para_outlier == True:
                        st.session_state['transf_normal_para_outlier'] = True
                    if transf_outlier_para_normal == True:
                        st.session_state['transf_outlier_para_normal'] = True

                    st.session_state['datas_para_transformar'] = pd.to_datetime(st.session_state['datas_modificadas']).normalize()
                    st.session_state['datas_modificadas'] = []
                    st.success("Transformações aplicadas com sucesso!")
                    time.sleep(1)
                    st.rerun()

                
                


            with col_transformacao2:

                with st.container(border=True):
                    st.subheader("Transformar dados normais em anomalias")

                    datas_normais = (outliers_atual.loc[(outliers_atual['Outlier_pontuador'] == 0), 'Data'])
                    datas_normais = datas_normais.dt.normalize()
                    inicio_janela = df_atual.loc[0, 'Data']
                    final_janela = df_atual.loc[len(df_atual) - 1, 'Data']
                    
                    d2 = st.date_input(
                        "Insira o intervalo a ser modificado",
                        (inicio_janela, final_janela),
                        min_value=inicio_janela,
                        max_value=final_janela,
                        format="DD/MM/YYYY",
                        key="data_input2"
                    )
                
                    datas2 = [pd.to_datetime(data).normalize() for data in d2]
                    datas2 = outliers_atual.loc[outliers_atual['Data'].between(datas2[0], datas2[1]), 'Data']
                    
                    for data in datas2:
                        if data.date() in datas_normais.dt.date.values:
                            media = df_atual.loc[(df_atual['Data'] == data), 'Media'].values[0]
                            bloquear_add2 = False
                        else:
                            st.error("Existem pontos anômalos no intervalo.")
                            bloquear_add2 = True
                            break
                    
                    subcol1, subcol2, subcol3 = st.columns([1,2,1])

                    with subcol1:
                        sucesso2 = False
                        if st.button("Adicionar datas na lista", disabled=bloquear_add2, key="fluxo2-botao1"):
                            for data in datas2:
                                st.session_state['datas_modificadas2'].append(data)
                            sucesso2 = True

                    if sucesso2:
                        st.success(f"Datas adicionadas na lista com sucesso!")

                    with subcol2:
                        with st.popover("Mostrar lista de datas atual"):
                            i = 1
                            for data_ in st.session_state['datas_modificadas2']:
                                st.write(f"Data nº {i}: {data_}")
                                i += 1

                    if len(st.session_state['datas_modificadas2']) > 0:
                        disabled_transformacao2 = False
                    else:
                        disabled_transformacao2 = True

                    if st.button("Aplicar transformação", key="fluxo2-botao2", type="primary", disabled=disabled_transformacao2):
                        st.session_state['datas_para_transformar2'] = pd.to_datetime(st.session_state['datas_modificadas2']).normalize()
                        st.session_state['datas_modificadas2'] = []
                        st.success("Transformações aplicadas com sucesso!")
                        time.sleep(1)
                        st.rerun()

        # =========== Visualização da série ===============

        st.subheader("Visualização da série")

        col1, col2 = st.columns(2)

        with col1:
            fig, _ = relatorio_anomalias(outliers_atual, df_atual, modelo)
            st.plotly_chart(fig)

        with col2:
            fig2, _ = relatorio_anomalias(outliers_atual, df_atual_corrigido, modelo)

            fig2.add_trace(go.Scatter(x=df_atual_corrigido['Data'][::-1], y=new_trace[::-1], name="correção", line=dict(
                            color="#19E5B5",
                            width=2
                        )))
            
            st.plotly_chart(fig2, key="fig_corrigida")
        
        # ============= Correção ===============

        if st.button("Aplicar correção nesta janela", type="primary"):

            # Atualiza a série original com os valores corrigidos
            if periodicidade == "Mês a mês":
                st.session_state['df_provisorio'].loc[(st.session_state['df_provisorio']["Data"].dt.month == mes) & (st.session_state['df_provisorio']["Data"].dt.year == ano), "Media"] = df_atual_corrigido["Media"].values
                st.session_state['serie_outliers'].loc[(st.session_state['serie_outliers']["Data"].dt.month == mes) & (st.session_state['serie_outliers']["Data"].dt.year == ano), "Media"] = None
                st.session_state['serie_outliers'].loc[(st.session_state['serie_outliers']["Data"].dt.month == mes) & (st.session_state['serie_outliers']["Data"].dt.year == ano), "Outlier_pontuador"] = df_atual_corrigido["Outlier_pontuador"].values
            elif periodicidade == "Ano a ano":
                st.session_state['df_provisorio'].loc[st.session_state['df_provisorio']["Data"].dt.year == ano, "Media"] = df_atual_corrigido["Media"].values
                st.session_state['serie_outliers'].loc[st.session_state['serie_outliers']["Data"].dt.year == ano, "Media"] = None
                st.session_state['serie_outliers'].loc[st.session_state['serie_outliers']["Data"].dt.year == ano, "Outlier_pontuador"] = df_atual_corrigido["Outlier_pontuador"].values #trocar para df_atual_corrigido? programa so modifica df_atual
                
            st.success('Janela atualizada com sucesso! Recarregando...')
            time.sleep(1)

            if metodo == "Regressão linear":
                st.session_state['uso_regressao'] = True
            elif metodo == "Interpolação polinomial":
                st.session_state['uso_interpolacao_polinomial'] = True
            elif metodo == "Interpolação por spline":
                st.session_state['uso_interpolacao_spline'] = True
            
            st.session_state['datas_modificadas'] = []
            st.session_state['datas_para_transformar'] = []
            st.session_state['datas_para_transformar2'] = []

            if st.session_state['janela'] > len(intervalos_outliers):
                st.session_state['janela'] = 0
                st.rerun()
            else:
                st.rerun()

        st.divider()
    else:
        st.warning("Não há mais pontos a modificar.")


    if st.button("Finalizar alterações e prosseguir", type='primary'):
        st.switch_page("pages/stage3.py")