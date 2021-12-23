from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np
from value_per_row_import import Value_per_row_import

from map import Map
texts_dict = ""

def show_map(df):
    cfg = cn.map_cfg
    station_map = Map(df, cfg)
    p = station_map.get_plot()
    st.bokeh_chart(p)


def show_summary():
    lst_station_fields = list(st.session_state.config.coltype2dict(cn.CTYPE_STATION).keys())
    df_stations = st.session_state.config.row_value_df[lst_station_fields].drop_duplicates()
    df_stations = show_filters(df_stations)
    st.markdown(f"Number of stations: {len(df_stations)}")
    AgGrid(df_stations)
    show_map(df_stations)

def show_filters(df):
    with st.sidebar.expander("🔎 Filter"):
        lst_stations = list(df[st.session_state.config.station_col].unique())
        lst_stations.sort()
        sel_stations = st.multiselect("Station", options=lst_stations)
        if len(sel_stations) > 0:
            df = df[df[st.session_state.config.station_col].isin(sel_stations)]
        return df

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
