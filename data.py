from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np
from value_per_row_import import Value_per_row_import

texts_dict = ""

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


def load_new_dataset():
    if st.session_state.step == 0:
        st.session_state.file_format = st.selectbox('sample format', cn.SAMPLE_FORMATS)
        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            st.session_state.df_raw = pd.read_csv(uploaded_file, sep=";")
            if st.button("Import Data"):
                if st.session_state.file_format == cn.SAMPLE_FORMATS[0]:
                    #mapped_parameters, sample_par_map = map_parameters(df, file_format)
                    df = calc_meql(st.session_state.df_raw)
                    df = calc_pct(st.session_state.df_raw)
                elif st.session_state.file_format == cn.SAMPLE_FORMATS[1]:
                    imp = Value_per_row_import(st.session_state.df_raw, texts_dict['value_per_row_import'])
                    imp.run_step()
                    # mapped_parameters, sample_par_map = map_parameters(df, file_format)   
    else:
        if st.session_state.file_format == cn.SAMPLE_FORMATS[0]:
            pass
            #mapped_parameters, sample_par_map = map_parameters(df, file_format)
            #df = calc_meql(df)
            #df = calc_pct(df)
        elif st.session_state.file_format == cn.SAMPLE_FORMATS[1]:
            imp = Value_per_row_import(st.session_state.df_raw, texts_dict['value_per_row_import'])
            imp.run_step()


def nwis_test():
    sites = ['331915112400601','332023112372901','320834110580401']
    siteInfo = nwis.get_info(sites=sites)
    st.write(siteInfo[0])
    
    wellDf = nwis.get_record(sites=sites, service='qwdata', start='2000-01-01')
    st.write(wellDf.columns)
    st.write(wellDf.head())
    st.write(wellDf[['p00025','p00003','p00010']])


def show_menu(td: dict):
    global texts_dict

    texts_dict = td
    MENU_OPTIONS = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        show_current_dataset()
    if menu_action == MENU_OPTIONS[1]:
        load_new_dataset()
    if menu_action == MENU_OPTIONS[3]:
        nwis_test()
    

    
