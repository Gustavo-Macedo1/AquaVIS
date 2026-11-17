from darts import TimeSeries
from darts.ad import KMeansScorer
from darts.ad.scorers.pyod_scorer import PyODScorer
from pyod.models.auto_encoder import AutoEncoder
from darts.ad import QuantileDetector
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import joblib

def cria_serie_temporal(df):
    # Criação do objeto TimeSeries utilizando 'Data' e 'Média'
    serie_temporal = TimeSeries.from_dataframe(df, 'Data', 'Media', freq='D', fill_missing_dates=True,)
    return serie_temporal

def interpola_serie_temporal(serie_temporal, metodo='linear', ordem=None):
    # Preenchimento de dados faltantes da série temporal via interpolação: 'linear', 'spline', etc.
    serie_frame = serie_temporal.to_series()

    if metodo == 'polynomial' or metodo == 'spline':
        if ordem is None:
            raise ValueError("A ordem do polinômio deve ser especificada para interpolação polinomial.")
        serie_frame.interpolate(method=metodo, order=ordem, inplace=True)
    else:
        serie_frame.interpolate(method=metodo, inplace=True)

    serie_frame = serie_frame.to_frame()
    serie_frame.reset_index(inplace=True)

    serie_interpolada = TimeSeries.from_dataframe(serie_frame, 'Data', 'Media', fill_missing_dates=True, freq='D')
    return serie_interpolada

def cria_serie_temporal_interpolada(df, metodo='linear', ordem=None):
    # Cria e interpola a série temporal
    serie_temporal = cria_serie_temporal(df)
    serie_interpolada = interpola_serie_temporal(serie_temporal, metodo, ordem)
    return serie_interpolada

def plota_serie_temporal_interpolada(df, metodo):
    fig = go.Figure()

    x = df.Data[::-1]
    y = df.Media[::-1]

    fig.add_trace(go.Scatter(x=x, y=y, name=metodo, line_shape=metodo))

    fig.show()

def plota_serie_temporal(serie):
    # Plot da TimeSeries
    plt.figure(figsize=(12, 6))
    serie.plot()
    plt.show()

def prepara_resultados(scorer, detector, serie_temporal):
    # Preparação dos dataframes de visualização
    score = scorer.score(serie_temporal)
    detector.fit(score)
    binary = detector.detect(score)

    df_bin = binary.to_dataframe()
    df_bin.reset_index(inplace=True)

    df_timeseries = serie_temporal.to_dataframe()
    df_timeseries.reset_index(inplace=True)

    df_series_binary = pd.merge(df_timeseries, df_bin, how='inner', on='Data')
    df_series_binary.rename(columns={'Media_x': 'Media', 'Media_y': 'Outlier_pontuador'}, inplace=True)

    df_series_binary2 = df_series_binary.copy()
    index_list = list(df_series_binary2[df_series_binary2['Outlier_pontuador'] == 0.0].index)

    for index in index_list:
        df_series_binary2.loc[index, 'Media'] = None

    return df_series_binary2, df_timeseries

def relatorio_anomalias(serie_outliers, serie_temporal, modelo, data_inicial=None, data_final=None):
    df_series_binary2, df_timeseries = serie_outliers, serie_temporal
    # Criação da figura
    fig = go.Figure()

    x = df_timeseries.Data[::-1]
    y = df_timeseries.Media[::-1]
    x_sb = df_series_binary2.Data[::-1]
    y_sb = df_series_binary2.Media[::-1]

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

    fig.update_layout(
        title=dict(text=f"Pré-visualização de detecção de anomalias com {modelo}"),
        xaxis=dict(title=dict(text="Tempo")),
        yaxis=dict(title=dict(text="Cota")),
        legend=dict(title=dict(text="Legenda")))

    media = df_series_binary2['Media'].mean()
    df_outliers = df_series_binary2[df_series_binary2['Outlier_pontuador'] != 0.0]

    desvio_maximo = abs(df_outliers['Media'].max() - df_outliers['Media'].mean())
    desvio_minimo = abs(df_outliers['Media'].min() - df_outliers['Media'].mean())
    fator = min(desvio_maximo, desvio_minimo)
    outliers = len(df_outliers)
    outliers_extremos = len(df_series_binary2[(df_series_binary2['Outlier_pontuador'] != 0.0) & ((abs(df_series_binary2['Media'] - media)) > 0.9 * fator)])
    desvio_outliers = round(df_outliers['Media'].std(), 2)

    relatorio_outliers = [outliers, outliers_extremos, desvio_outliers]
    return fig, relatorio_outliers

def completar_data(df_maior, df_menor):
        data_inicial_menor = df_menor.loc[0, 'Data']
        data_inicial_maior = df_maior.loc[0, 'Data']

        linhas = df_maior.loc[df_maior['Data'].between(data_inicial_maior, data_inicial_menor, inclusive='left')]
        linhas['Outlier_pontuador'] = 0
        linhas['Media'] = None

        df_completo = pd.concat([linhas, df_menor])
        df_completo.reset_index(drop=True, inplace=True)

        return df_completo

def preparar_serie(df):
    df1 = df.loc[df['Media'].first_valid_index():]
    df1 = df1.groupby('Data')['Media'].mean().reset_index()
    serie_temporal = cria_serie_temporal_interpolada(df1, 'linear')
    return serie_temporal

def preparar_dados():
    df1 = pd.read_csv(f"./data/csv_train/cotas_1.csv", encoding='ISO-8859-1', delimiter=',')
    df2 = pd.read_csv(f"./data/csv_train/cotas_2.csv", encoding='ISO-8859-1', delimiter=',')
    df3 = pd.read_csv(f"./data/csv_train/cotas_3.csv", encoding='ISO-8859-1', delimiter=',')
    df4 = pd.read_csv(f"./data/csv_train/cotas_4.csv", encoding='ISO-8859-1', delimiter=',')
    df5 = pd.read_csv(f"./data/csv_train/cotas_5.csv", encoding='ISO-8859-1', delimiter=',')

    # DF1
    df1 = df1.groupby('Data')['Media'].mean().reset_index()
    serie_temporal = cria_serie_temporal_interpolada(df1, 'linear')

    # DF2
    df2['Data'] = pd.to_datetime(df2['Data'])
    df2.loc[df2['Data'] == '1982-07-01', 'Media'] = df2[df2['Data'].dt.month == 7]['Media'].mean()
    df2 = df2.groupby('Data')['Media'].mean().reset_index()
    serie_temporal2 = cria_serie_temporal_interpolada(df2, 'linear')

    # DF3
    df3['Data'] = pd.to_datetime(df3['Data'])
    df3.loc[df3['Data'] == '1967-11-01', 'Media'] = df3[df3['Data'].dt.month == 11]['Media'].mean()
    df3 = df3.groupby('Data')['Media'].mean().reset_index()
    serie_temporal3 = cria_serie_temporal_interpolada(df3, 'linear')

    # DF4
    df4 = df4.groupby('Data')['Media'].mean().reset_index()
    serie_temporal4 = cria_serie_temporal_interpolada(df4, 'linear')

    # DF5
    df5['Data'] = pd.to_datetime(df5['Data'])
    df5.loc[df5['Data'] == '1980-07-01', 'Media'] = df5[df5['Data'].dt.month == 7]['Media'].mean()
    df5 = df5.groupby('Data')['Media'].mean().reset_index()
    serie_temporal5 = cria_serie_temporal_interpolada(df5, 'linear')

    series = [serie_temporal, serie_temporal2, serie_temporal3, serie_temporal4, serie_temporal5]
    return series

def preparar_detector(scorer, serie_temporal):
    score = scorer.score(serie_temporal)
    detector = QuantileDetector(high_quantile=0.8)
    detector.fit(score)
    return detector


def treina_kmeans(series):
    series = series[1:]

    kmeans_scorer = KMeansScorer(k=8, window=25)
    kmeans_scorer.fit(series)

    joblib.dump(kmeans_scorer, 'novos/kmeans_scorer.pkl')

def treina_autoencoder(series):
    auto_encoder = AutoEncoder(epoch_num=20, batch_size=32, lr=0.0001)
    auto_encoder_scorer = PyODScorer(auto_encoder, window=13)
    auto_encoder_scorer.fit([series[1], series[4]])

    joblib.dump(auto_encoder_scorer, 'novos/auto_encoder_scorer.pkl')

def workflow():
    series = preparar_dados()
    treina_kmeans(series)
    treina_autoencoder(series)

