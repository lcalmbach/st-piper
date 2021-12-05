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

def show_summary():
    lst_station_fields = list(st.session_state.config.coltype2dict(cn.CTYPE_STATION).keys())
    df_stations = st.session_state.config.row_value_df[lst_station_fields].drop_duplicates()
    st.markdown(f"Number of stations: {len(df_stations)}")
    AgGrid(df_stations)

def show_filters(df):
    x = st.session_state.config.key2col()
    station_key = x[cn.STATION_IDENTIFIER_COL]
    if st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
        date_key = x[cn.SAMPLE_DATE_COL]
    #st.write(list(df[sample_key]))
    lst_stations = list(df[station_key].unique())
    stations = st.sidebar.multiselect("Station", options=lst_stations)
    lst_station_fields = list(st.session_state.config.coltype2dict(cn.CTYPE_STATION).keys())
    fields = st.sidebar.multiselect("Fields", options=lst_station_fields)
    df_stations = st.session_state.config.row_sample_df
    df_stations = df_stations[fields] if len(fields)>0 else df_stations[lst_station_fields]
    df_stations.drop_duplicates(inplace=True)
    if len(stations)>0:
        pass #filter
    st.markdown(f"Stations in current dataset: {len(df_stations)}")
    AgGrid(df_stations)

def show_menu(td: dict):
    global texts_dict
    texts_dict = td

    menu_options = td['menu_options']
    sel_option = st.sidebar.selectbox("Options", menu_options)
    if sel_option == td['menu_options'][0]:
        st.markdown("### Stations summary")
        show_summary()
    elif sel_option == td['menu_options'][1]:
        pass
