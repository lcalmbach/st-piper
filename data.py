import streamlit as st
import pandas as pd
import const as cn
import helper
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid


def check_data_format(df):
    ok = True
    err_msg = ''
    return ok, err_msg


def calc_meql(df:pd.DataFrame):
    """
    Adds a new column xx_mdqpl for all major ions xx
    """
    
    pmd = st.session_state.parameters_metadata
    df['ca_meqpl'] = df['ca'] / pmd['fmw']['ca'] * abs(pmd['valence']['ca'])
    df['na_meqpl'] = df['ca'] / pmd['fmw']['na'] * abs(pmd['valence']['na'])
    df['k_meqpl'] = df['k'] / pmd['fmw']['k'] * abs(pmd['valence']['k'])
    df['mg_meqpl'] = df['mg'] / pmd['fmw']['mg'] * abs(pmd['valence']['mg'])
    df['alk_meqpl'] = df['alk'] / pmd['fmw']['alk'] * abs(pmd['valence']['alk'])
    df['cl_meqpl'] = df['cl'] / pmd['fmw']['cl'] * abs(pmd['valence']['cl'])
    df['so4_meqpl'] = df['so4'] / pmd['fmw']['so4'] * abs(pmd['valence']['so4'])
    df['na_k_meqpl'] = df['na_meqpl']  + df['k_meqpl'] 
    return df


def calc_pct(df:pd.DataFrame):
    sum_cations = df['ca_meqpl'] + df['na_k_meqpl'] + df['mg_meqpl']
    df['ca_pct'] = df['ca_meqpl'] / sum_cations * 100
    df['na_pct'] = df['na_meqpl'] / sum_cations * 100
    df['k_pct'] = df['k_meqpl'] / sum_cations * 100
    df['mg_pct'] = df['mg_meqpl'] / sum_cations * 100
    df['na_k_pct'] = df['na_k_meqpl'] / sum_cations * 100
    
    sum_anions = df['alk_meqpl'] + df['cl_meqpl'] + df['so4_meqpl']
    df['alk_pct'] = df['alk_meqpl'] / sum_anions * 100
    df['cl_pct'] = df['cl_meqpl'] / sum_anions * 100
    df['so4_pct'] = df['so4_meqpl'] / sum_anions * 100
    return df


def show_current_dataset():
    df = st.session_state.current_dataset
    st.markdown("#### Current dataset")
    AgGrid(st.session_state.current_dataset)

    
    df_metadata = pd.DataFrame(df.columns)
    df_metadata.columns = ['column']
    df_metadata['parameter'] = df_metadata['column']
    df_metadata['column'].str.lower()
    df_metadata['fmw'] = df_metadata['column'].str.lower()
    st.markdown("#### Parameters")
    AgGrid((df_metadata))


def map_parameters(df):
    lst_without_not_used = df.columns
    lst_with_not_used =  ['Not Used']
    lst_with_not_used.extend(df.columns)
    station_column = st.selectbox("station column", lst_without_not_used)
    value_column = st.selectbox("value column", lst_without_not_used)
    parameter_column = st.selectbox("parameter name column", lst_without_not_used)
    casnr_column = st.selectbox("CasNr column", lst_with_not_used)
    
    stations = df[station_column].unique()
    parameters = pd.DataFrame(df[parameter_column].unique())
    parameters['key'] = lst_with_not_used[0]
    parameters.columns = ['parameter','key']
    parameters = parameters[parameters["parameter"].notnull()]
    if casnr_column != lst_with_not_used[0]:
        pass

    pmd = st.session_state.parameters_metadata
    num_pmd = pmd.query("type == 'chem'")
    lst = ['Not Used']
    lst.extend(list(num_pmd['name']))
    st.markdown("#### Map parameters")
    parameters = parameters.set_index('parameter')
    for idx, par in parameters.iterrows():
        parameters.loc[idx]['key'] = st.selectbox(idx, options=lst)
    parameters = parameters[parameters['key'] != 'Not Used']
    return parameters, station_column, value_column,parameter_column


def unmelt_data(df,parameters, station_column, value_column,parameter_column):
    df = df.pivot(index=station_column, columns=parameter_column)

def load_new_dataset():
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep=";")
        file_format = st.sidebar.selectbox('sample format', cn.SAMPLE_FORMATS)
        if file_format == cn.SAMPLE_FORMATS[0]:
            df = calc_meql(df)
            df = calc_pct(df)

        if file_format == cn.SAMPLE_FORMATS[1]:  
            parameters, station_column, value_column,parameter_column = map_parameters(df)  
            st.write(parameters)
            if st.button('Transform'):
                df = df[[station_column, parameter_column, value_column]]
                st.write(df)
                df = unmelt_data(df,parameters, station_column, value_column, parameter_column)

        ok, err_msg = check_data_format(df)
        if ok:
            st.write(f"{len(df)} records imported")
            AgGrid(df.head(1000))
            st.session_state.current_dataset = df
        else:
            warning_msg = f"This file could not be loaded, the following error occurred: '{err_msg}'"
            st.warning(warning_msg)
    
        

def nwis_test():
    sites = ['331915112400601','332023112372901','320834110580401']
    siteInfo = nwis.get_info(sites=sites)
    st.write(siteInfo[0])
    
    wellDf = nwis.get_record(sites=sites, service='qwdata', start='2000-01-01')
    st.write(wellDf.columns)
    st.write(wellDf.head())
    st.write(wellDf[['p00025','p00003','p00010']])

def show_menu(texts_dict: dict):
    MENU_OPTIONS = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        show_current_dataset()
    if menu_action == MENU_OPTIONS[1]:
        load_new_dataset()
    if menu_action == MENU_OPTIONS[3]:
        nwis_test()
    

    
