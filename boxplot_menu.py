from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
import xyzservices.providers as xyz
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, GMapOptions
from bokeh.plotting import gmap
from streamlit.delta_generator import MAX_DELTA_BYTES
from datetime import datetime, timedelta

import helper
import const as cn
from map import Map


def filter_stations(df: pd.DataFrame):
    with st.sidebar.expander("🔎 Filter"):
        station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
        station_options = st.session_state.config.get_station_list()
        sel_stations = st.sidebar.multiselect("Stations", station_options)
        if st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
            date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
            df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
            min_date = df[date_col].min().to_pydatetime().date()
            max_date = df[date_col].max().to_pydatetime().date()
            
            from_date = st.sidebar.date_input("From date", min_date)
            to_date = st.sidebar.date_input("From date", max_date)
            if (from_date != min_date) or (to_date != max_date):
                df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]
        if len(sel_stations)>0:
            df = df[df[station_col].isin(sel_stations)]
        return df

def get_locations_map_cfg():
    return cn.map_cfg

def show_locations_map():
    df = filter_stations(st.session_state.config.row_sample_df)
    cfg = get_locations_map_cfg()
    map = Map(df, cfg)
    p = map.get_map()
    st.bokeh_chart(p)
    helper.show_save_file_button(p)

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    
    if menu_action == menu_options[0]:
        show_locations_map()
        
    

