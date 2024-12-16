import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from PIL import Image
from io import BytesIO

# Configuração da página deve ser a primeira função Streamlit chamada
st.set_page_config(
    page_title='Telemarketing Analysis',
    layout='wide',
    initial_sidebar_state='expanded'
)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer._save()
    processed_data = output.getvalue()
    return processed_data

def recencia_class(x, r, q_dict):
    """Classifica como melhor o menor quartil
    x = valor da linha
    r = recência
    q_dict = quartil dicionário
    """
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

def freq_val_class(x, fv, q_dict):
    """Classifica como melhor o maior quartil
    x = valor da linha
    fv = frequência de valor
    q_dict = quartil dicionário
    """
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

def main():
    # Título
    st.write("""
    # RFV - Recência, Frequência e Valor
    """)
    st.markdown("---")

    # Botão de carregar arquivo
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    # Verifica se tem conteúdo carregado na aplicação
    if data_file_1 is not None:
        df_compras = pd.read_csv(data_file_1, infer_datetime_format=True, parse_dates=['DiaCompra'])
        
        st.write("## Recência (R)")
        dia_atual = df_compras['DiaCompra'].max()
        st.write("Dia máximo na base de dados:", dia_atual)

        st.write("Quantos dias faz que o cliente fez a sua última compra?")
        df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        st.write(df_recencia.head())

        df_recencia.drop(['DiaUltimaCompra'], axis=1, inplace=True)

        st.write("## Frequência (F)")
        st.write("Quantas vezes o cliente fez compras com a gente?")
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia.head())

        st.write("## Valor (V)")
        st.write("Quanto o cliente gastou no período?")
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor.head())

        st.write("## RFV")
        df_rf = df_recencia.merge(df_frequencia, on="ID_cliente")
        df_rfv = df_rf.merge(df_valor, on="ID_cliente")
        df_rfv.set_index('ID_cliente', inplace=True)
        st.write(df_rfv.head())

        st.write("## Segmentação usando RFV")
        st.write("Criando quartis para cada componente do RFV:")
        quartis = df_rfv.quantile([0.25, 0.50, 0.75])
        st.write(quartis)

        df_rfv['R_Quartile'] = df_rfv['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df_rfv['F_Quartile'] = df_rfv['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
        df_rfv['V_Quartile'] = df_rfv['Valor'].apply(freq_val_class, args=('Valor', quartis))
        df_rfv['RFV_Score'] = df_rfv['R_Quartile'] + df_rfv['F_Quartile'] + df_rfv['V_Quartile']
        st.write(df_rfv.head())

        st.write("Quantidade de clientes por grupos:")
        st.write(df_rfv['RFV_Score'].value_counts())

        st.write("#### Clientes com menor recência, maior frequência e maior valor gasto:")
        st.write(df_rfv[df_rfv['RFV_Score'] == 'AAA'].sort_values('Valor', ascending=False).head(10))

        st.write("### acoes de marketing/CRM")
        dict_acoes = {
            'AAA': 'Enviar cupons de desconto, pedir para indicar nosso produto para algum amigo.',
            'DDD': 'Churn! Clientes que gastaram bem pouco e fizeram poucas compras, fazer nada.',
            'DAA': 'Churn! Clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar.',
            'CAA': 'Churn! Clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar.'
        }
        df_rfv['acoes de marketing/crm'] = df_rfv['RFV_Score'].map(dict_acoes)
        st.write(df_rfv.head())

        # Exportar para csv
        df_xlsx = to_excel(df_rfv)
         st.download_button(
            label='Download Excel',
            data=df_xlsx,
            file_name='rfv_analysis.xlsx'
        
        st.write("Quantidade de clientes por tipo de ação:")
        st.write(df_rfv['acoes de marketing/crm'].value_counts(dropna=False))

if __name__ == '__main__':
    main()
