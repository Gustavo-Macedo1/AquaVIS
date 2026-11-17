import plotly.graph_objects as go
import streamlit as st
import pandas as pd

def criar_grafico(df, codigo=14100000, color=False):
    # Criação do objeto e definição dos eixos e da linha

    fig = go.Figure()

    x = df.Data[::-1]
    y = df.Media[::-1]

    if color == False:
        fig.add_trace(go.Scatter(x=x, y=y,
                            mode='lines',
                            name='Valor da cota média'))
    
    else:
        # fig.add_trace(go.Scatter(x=x, y=y,
        #                     mode='lines',
        #                     name='Valor da cota média'),
        #                     line=dict(
        #                         color="#19E5B5",
        #                         width=2
        #                     )
        #              )
        
        fig.add_trace(go.Scatter(x=x, y=y, name='Valor da cota média', line=dict(
                        color="#19E5B5",
                        width=2
                    )))

    annotations = []

    # Titulo
    annotations.append(dict(xref='paper', yref='paper', x=-0.10, y=1.05,
                                xanchor='left', yanchor='bottom',
                                text=f'Série Temporal de Cotas Médias - Estação: {codigo}',
                                font=dict(family='Arial',
                                            size=24,
                                            color='rgb(255,255,255)'),
                                showarrow=False))

    fig.update_layout(title_text=f"Série Temporal de Cotas Médias - Estação: {codigo}",
                    title_x=0.25,
                    title_y=0.85,
                    yaxis_title="Cota Média",
                    xaxis_title="Data",
                    font=dict(
                    family="Arial",
                    size=12))
    
    return fig

def mostrar_correcoes(serie_outliers, serie_temporal, modelo, metodo, order=None, data_inicial=None, data_final=None):
    mapa = {'Regressão linear' : 'linear', 'Interpolação polinomial' : 'polynomial', 'Interpolação por spline' : 'spline'}
    method = mapa[metodo]

    df_series_binary2, df_timeseries = serie_outliers, serie_temporal
    # Criação da figura
    fig = go.Figure()

    x = df_timeseries.Data[::-1]
    y = df_timeseries.Media[::-1]
    x_sb = df_series_binary2.Data[::-1]
    y_sb = df_series_binary2.Media[::-1]
    new_trace_x = x.copy()

    temp_df = pd.DataFrame({'Data': x, 'Media': y})
    temp_df['outliers'] = y_sb
    temp_df['new_trace'] = temp_df['outliers']
    st.write(temp_df)

    inicio_mes = temp_df['Data'].iloc[0]
    final_mes = temp_df['Data'].iloc[len(temp_df) - 1]
    indexes = []

    for row in temp_df.iterrows():
        if row[1]['Data'] not in [inicio_mes, final_mes]:
            if row[1]['outliers'] > 0:
                temp_df.loc[row[0], 'new_trace'] = 1
                temp_df.loc[row[0], 'Media'] = None
                indexes.append(row[0])

    if method == 'linear':
        temp_df['Media'] = temp_df['Media'].interpolate(method=method, order=3)
    else:
        temp_df['Media'] = temp_df['Media'].interpolate(method=method, order=order)

    for index in indexes:
        temp_df.loc[index, 'new_trace'] = temp_df.loc[index, 'Media']
        if index != indexes[-1] and index != indexes[0]:
            y.loc[index] = None

    new_trace_y = temp_df['new_trace'][::-1]


    if data_inicial and data_final:
        mask = (x >= data_inicial) & (x <= data_final)
        x = x[mask]
        y = y[mask]
        x_sb = x_sb[mask]
        y_sb = y_sb[mask]

    fig.add_trace(go.Scatter(x=x, y=y, name="real"))
    fig.add_trace(go.Scatter(x=x_sb, y=y_sb, name="outlier", line=dict(
                        color='#FF4500',
                        width=2
                    )))
    fig.add_trace(go.Scatter(x=new_trace_x, y=new_trace_y, name="correção", line=dict(
                        color="#19E5B5",
                        width=2
                    )))

    fig.update_layout(
        title=dict(text=f"Pré-visualização de detecção de anomalias com {modelo}"),
        xaxis=dict(title=dict(text="Tempo")),
        yaxis=dict(title=dict(text="Cota")),
        legend=dict(title=dict(text="Legenda")))

    st.write(fig)