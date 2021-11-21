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

def show_filters(df):
    lst_stations = list(df[st.session_state.key2col['Station identifier']]).unique()
    lst_samples = list(df[st.session_state.key2col['Sampling date']]).unique()
    station = st.sidebar.selectbox("Station",options=lst_stations)
    sampling_date = st.sidebar.selectbox("Sampling date", options=lst_samples)

def show_menu(td: dict):
    global texts_dict

    if st.session_state.file_format == cn.SAMPLE_FORMATS[1]:
        df = st.session_state.df_raw
    else:
        df = st.session_state.df_melted
    

    texts_dict = td
    show_filters(df)
    
    

    
