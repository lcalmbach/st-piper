from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
from st_aggrid import AgGrid
import numpy as np

texts_dict = ""

def show_summary():
    lst_sample_fields = list(st.session_state.config.coltype2dict(cn.CTYPE_SAMPLE).keys())
    station_identifier_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
    lst_sample_fields.insert(0,station_identifier_col)
    df_samples = st.session_state.config.row_value_df[lst_sample_fields].drop_duplicates()
    df_samples = df_samples.sort_values(station_identifier_col)
    st.markdown(f"Number of samples: {len(df_samples)}")
    AgGrid(df_samples)

def show_detail():
    df = st.session_state.config.row_value_df
    x = st.session_state.config.key2col()
    station_key = x['Station identifier']
    sample_key = x['Sampling date']
    # st.write(list(df[sample_key]))
    lst_stations = list(df[station_key].unique())
    station = st.sidebar.selectbox("Station", options=lst_stations)
    lst_samples = list(df[df[station_key] == station][sample_key].unique())
    lst_samples.sort()
    sampling_date = st.sidebar.selectbox("Sample", options=lst_samples)
    df = st.session_state.config.row_value_df
    df = df[(df[station_key] == station) & (df[sample_key]==sampling_date)]
    df_sample = df[st.session_state.config.get_parameter_detail_form_columns()]
    st.markdown(f"Station: {df.iloc[0][station_key]}")
    st.markdown(f"Sample date: {df.iloc[0][sample_key]}")

    AgGrid(df_sample)

def show_menu(td: dict):
    global texts_dict
    texts_dict = td
    menu_options = td['menu_options']
    sel_option = st.sidebar.selectbox("Options", menu_options)
    if sel_option == td['menu_options'][0]:
        st.markdown("### Samples summary")
        show_summary()
    elif sel_option == td['menu_options'][1]:
        st.markdown("### Sample Detail")
        show_detail()
