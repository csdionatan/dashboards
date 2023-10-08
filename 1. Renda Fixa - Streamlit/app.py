import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go
from enum import Enum
from dateutil import relativedelta
import seaborn as sns;sns.set()
import table_builder as tb
import numpy as np
import os



class path(Enum):
    LOCAL = os.path.dirname(__file__)+ '/data/'
    
    
################### CONFIGURAÇÕES DA PÁGINA #################
st.set_page_config(page_title='Renda Fixa',page_icon=':chart_with_upwards_trend:',layout='wide')
st.title('RENDA FIXA - ACOMPANHAMENTO :chart_with_upwards_trend:')
hide_st_style = """
            <style>
            footer {visibility: visible;}
            footer:after{
                content:'Made by Dionatan Silva';
                display:block;
                position:relative;
                color:tomato;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)




# tipo = [st.sidebar.selectbox('Tipo',['LFT','NTN-B'])]


################### COLETANDO E ORGANIZANDO DADOS #################

HOLIDAYS = pd.read_parquet(path.LOCAL.value + 'misc/BR_HOLIDAYS.parquet')['Data'].apply(lambda x: pd.to_datetime(x))
HOLIDAYS = pd.DataFrame(HOLIDAYS).set_index('Data')



ANBIMA_DATA = pd.read_parquet(path.LOCAL.value+'/anbima/titulos_publicos/')
ANBIMA_DATA['data_referencia'] = pd.to_datetime(ANBIMA_DATA['data_referencia'])
ANBIMA_DATA['data_vencimento'] = pd.to_datetime(ANBIMA_DATA['data_vencimento'])

TPF = pd.read_parquet(path.LOCAL.value + '/selic/tpf_extragrupo')
TPF['Financeiro'] = TPF['pu_med']*TPF['quant_negociada']

ANBIMA_DATA = ANBIMA_DATA.merge(TPF,left_on=['tipo_titulo','data_referencia','data_vencimento'],right_on=['sigla','data_mov','vencimento'],how='left')


df_financeiro = ANBIMA_DATA.pivot_table(index='data_referencia',values='Financeiro',columns='tipo_titulo').melt(ignore_index=False).loc['2023-06':].reset_index()


indices = pd.read_parquet(path.LOCAL.value+"/indices")
lista_indices = ["CDI",'IMA-S','IMA-B 5','IMA-B','IDA-DI','IDkA IPCA 5A']
indices = indices.query('variable in @lista_indices').pivot_table(index='data_referencia',values='value',columns='variable').dropna()

cdi = indices['CDI'].pct_change()

LFTS = ANBIMA_DATA.loc[ANBIMA_DATA.tipo_titulo == 'LFT'].pivot_table(index='data_referencia',values = 'pu', columns='data_vencimento')


################### FIGURAS DE Indices #################
fig_indices = px.line(indices.last('12m').pct_change().add(1).cumprod())

################### FIGURAS DE TPF #################
fig_financeiro = px.bar(df_financeiro,
                        x='data_referencia',
                        y='value',color='tipo_titulo',
                        title='Volume Financeiro - Diário'
                        )

fig_financeiro_semanal = px.bar(df_financeiro.groupby([pd.Grouper(key='data_referencia', freq='W'),'tipo_titulo'])['value'].sum().reset_index(),
                                x='data_referencia',
                                y='value',color='tipo_titulo',
                                title='Volume Financeiro - Semanal'
                                )

for f in [fig_financeiro, fig_financeiro_semanal]:
    f.update_layout(
        yaxis=dict(
            title='Financeiro',
            titlefont_size=16,
            tickfont_size=14,
            ),
        xaxis=dict(title='Data')
        )
    
    
l = LFTS.tail(22).pct_change()
l = l.div(cdi,axis=0,).dropna(how='all',axis=1).dropna(how='all',axis=0)
l.columns = [str(c.strftime('LFT - %b%y')) for c in l.columns]
l = l*100
l = l.round(2)
l = l.replace(0,np.nan)
l = l.T
l.columns = [str(c.strftime('%Y-%m-%d')) for c in l.columns]
# lfts_heatmap = px.imshow(l,
#                          text_auto=True,
#                          color_continuous_scale='RdYlBu')
lfts_heatmap = go.Figure(
    go.Heatmap(
        z=l.values[::-1],
        text=l.values[::-1],
        x=l.columns.values,
        # xtype='array',
        y=l.index[::-1],
        zmid=100.,
        texttemplate="%{text}",
        colorscale='RdBu'
        
        )
    )
lfts_heatmap.update_xaxes(type='category')
lfts_heatmap.update_layout(
    xaxis={
        # 'rangebreaks':[dict(bounds=["sat", "mon"]),
                    #    dict(values = HOLIDAYS.loc[l.columns[0]:l.columns[-1]].index.strftime("%Y-%m-%d").values)
                    #   ],
        # 'tickangle':-45
    })

    
    
################### FIGURAS DE LEILOES #################
financeiro = (pd.read_parquet(path.LOCAL.value+'tesouronacional/leilloes/',
                filters=[
                    ('data_do_leilao','>=',pd.to_datetime('2022-07-25')),
#                     ('titulo','==','LFT'),
#                     ('data_de_vencimento','==',pd.to_datetime('2033-05-15')),
                    ('volta','==','1.ª volta'),
                    ('financeiro',"!=",0)
                ]
               )
.pivot_table(columns='titulo',index='data_do_leilao',values='financeiro')
# .drop(columns=columns)
.dropna(how='all')
)
financeiro = financeiro.rename(columns={"LTN":"PRÉ","NTN-F":'PRÉ'}).fillna(0)

financeiro = financeiro.groupby(financeiro.columns,axis=1).sum()

financeiro = financeiro.resample('m').sum()


financeiro = financeiro.divide(financeiro.sum(axis=1),axis=0)
x = financeiro.index.strftime("%b/%y")
fig = go.Figure()
for i in financeiro.columns:
    fig.add_trace(go.Bar(x=x,y=financeiro[i],name=i,text=((100*financeiro[i])).round(1)))
fig.update_layout(barmode='stack')



fig.update_layout(
    title_text="Percentual do Indexador no Leilão Mensal",
    font=dict(
        family="Calibri",
        size=14.5,
        color="black")
)








################### FIGURAS DE JUROS #################
idka = pd.read_parquet(path.LOCAL.value+'anbima/indices/idka').pivot_table(columns='nome',index='data_referencia',values='tx_venda')
idka_pre = idka['IDkA Pré 5A']
idka_ipca = idka['IDkA IPCA 5A']
df = pd.concat([idka_ipca,idka_pre],axis=1)
df.columns = ['Juro Real','Juro Nominal']
df['Infl. Implícita'] = df['Juro Nominal'] - df['Juro Real']
x = (df.iloc[-66:].diff().fillna(0).cumsum()*100)
fig_j = px.bar(x.reset_index(),x='data_referencia',y=['Infl. Implícita','Juro Real'])



fig_j.add_scatter(x=x.index,y=x['Juro Nominal'],marker={'color':'black'},name='Juro Nominal')

fig_j.update_layout(    
    legend = {
        'title':''
    },
    title='Acumulado de Variação 5y - 60du',
    xaxis_title='Data',
    yaxis_title='BPS',
    xaxis={
        'rangebreaks':[dict(bounds=["sat", "mon"]),
                       dict(values = HOLIDAYS.loc[x.index[0]:x.index[-1]].index.strftime("%Y-%m-%d").values)
                      ],
        'tickangle':-45
    },
    font=dict(
        family="Calibri",
        size=14.5,
        color="black")
)


dka_pre = idka['IDkA Pré 2A']
idka_ipca = idka['IDkA IPCA 2A']
df = pd.concat([idka_ipca,idka_pre],axis=1)
df.columns = ['Juro Real','Juro Nominal']
df['Infl. Implícita'] = df['Juro Nominal'] - df['Juro Real']
x = (df.loc['2022-09':].diff().fillna(0).cumsum()*100)
fig_j2 = px.bar(x.reset_index(),x='data_referencia',y=['Infl. Implícita','Juro Real'])



fig_j2.add_scatter(x=x.index,y=x['Juro Nominal'],marker={'color':'black'},name='Juro Nominal')

fig_j2.update_layout(    
    legend = {
        'title':''
    },
    title='Acumulado de Variação 2y - 2023',
    xaxis_title='Data',
    yaxis_title='BPS',
    xaxis={
        'rangebreaks':[dict(bounds=["sat", "mon"]),
                       dict(values = HOLIDAYS.loc[x.index[0]:x.index[-1]].index.strftime("%Y-%m-%d").values)
                      ],
        'tickangle':-45
    },
    font=dict(
        family="Calibri",
        size=14.5,
        color="black")
)

ettj = pd.read_parquet(path.LOCAL.value+'anbima/ettj/')
last_day = ettj['data_referencia'].max()
BUSDAYS = pd.read_parquet(path.LOCAL.value + '/misc/BR_BUSDAYS')['Dias Uteis'].apply(lambda x: pd.to_datetime(x))
ettj_1d = ettj.loc[ettj['data_referencia'] == last_day]
ettj_1w = ettj.loc[ettj['data_referencia']==BUSDAYS.loc[BUSDAYS<=last_day].iloc[-5]]
ettj_1m = ettj.loc[ettj['data_referencia']==BUSDAYS.loc[BUSDAYS<(last_day - relativedelta.relativedelta(months=1))].iloc[-1]]

ettj_pre = pd.DataFrame(index=ettj_1d['vertice_du'])
ettj_pre['D -1'] = ettj_1d['taxa_prefixadas'].values
ettj_pre['W -1'] = ettj_1w['taxa_prefixadas'].values
ettj_pre['M -1'] = ettj_1m['taxa_prefixadas'].values
ettj_pre = ettj_pre.dropna()
ettj_pre.index= ettj_pre.index/252

ettj_real = pd.DataFrame(index=ettj_1d['vertice_du'])
ettj_real['D -1'] = ettj_1d['taxa_ipca'].values
ettj_real['W -1'] = ettj_1w['taxa_ipca'].values
ettj_real['M -1'] = ettj_1m['taxa_ipca'].values
ettj_real = ettj_real.dropna()
ettj_real.index= ettj_real.index/252

ettj_implicita = pd.DataFrame(index=ettj_1d['vertice_du'])
ettj_implicita['D -1'] = ettj_1d['taxa_implicita'].values
ettj_implicita['W -1'] = ettj_1w['taxa_implicita'].values
ettj_implicita['M -1'] = ettj_1m['taxa_implicita'].values
ettj_implicita = ettj_implicita.dropna()
ettj_implicita.index= ettj_implicita.index/252

ettj_pre_fig = px.line(ettj_pre)
ettj_real_fig = px.line(ettj_real)
ettj_impl_fig = px.line(ettj_implicita)

for f in [ettj_pre_fig, ettj_real_fig, ettj_impl_fig]:
    f.update_layout(xaxis_title='Anos',yaxis_title = 'Taxa')









################### ORGANIZANDO O DASHBOARD #################    
tab0, tab1, tab2, tab3 = st.tabs(["Índices","Títulos Públicos - Geral", "Leilões", "Juros"])


col_00 = tab0.columns(1)[0]
col_01,col_02 = tab0.columns([1,1.5])


col_00.plotly_chart(fig_indices,use_container_width=True)

df = (indices.resample('m').last().pct_change().tail(6).T*100).round(3)
df.index.name = 'Resultados 5m'
df.columns = [c.strftime('%Y-%m') for c in df.columns]


col_01.plotly_chart(px.imshow(df,text_auto=True),use_container_width=True)
indexes_table = tb.builder(indices)
col_02.write(indexes_table,use_container_width=True)




col_11,col_12 = tab1.columns(2)
col_13 = tab1.columns(1)[0]

col_21,col_22 = tab2.columns(2)



col_31,col_32 = tab3.columns(2)
tab3.divider()
tab31,tab32,tab33 = tab3.tabs(['Juro Nominal','Juro Real','Implícita'])
col_33,col_34 = tab31.columns(2)
col_35,col_36 = tab32.columns(2)
col_37,col_38 = tab33.columns(2)


#Inserindo gráficos
col_11.plotly_chart(fig_financeiro,use_container_width=True)
col_12.plotly_chart(fig_financeiro_semanal,use_container_width=True)

col_13.plotly_chart(lfts_heatmap,use_container_width=True)



col_21.plotly_chart(fig,use_container_width=True,theme=None)


## Juros tab
col_31.plotly_chart(fig_j2,use_container_width=True,theme=None)
col_32.plotly_chart(fig_j,use_container_width=True,theme=None)

col_33.plotly_chart(ettj_pre_fig,use_container_width=True,theme=None)
col_35.plotly_chart(ettj_real_fig,use_container_width=True,theme=None)
col_37.plotly_chart(ettj_impl_fig,use_container_width=True,theme=None)
