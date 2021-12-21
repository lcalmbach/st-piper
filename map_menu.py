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


def show_filter(df: pd.DataFrame, filters: list):
    with st.sidebar.expander("🔎 Filter"):
        if 'station' in filters:
            station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
            station_options = st.session_state.config.get_station_list()
            sel_stations = st.multiselect("Stations", station_options)
            if len(sel_stations)>0:
                df = df[df[station_col].isin(sel_stations)]
        
        if 'date' in filters and st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
            date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
            df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
            min_date = df[date_col].min().to_pydatetime().date()
            max_date = df[date_col].max().to_pydatetime().date()
            
            from_date = st.date_input("From date", min_date)
            to_date = st.date_input("From date", max_date)
            if (from_date != min_date) or (to_date != max_date):
                df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]

        return df

def get_location_map_cfg():
    return cn.map_cfg

def get_parameter_map_cfg(cfg, df):
    with st.sidebar.expander("⚙️ Settings"):
        cfg['prop_size_method'] = st.radio("Proportinal color or size", ['Color', 'Size']).lower()
        cfg['aggregation'] = st.radio("Aggregation", ['mean', 'max', 'min'], help='Aggregation for stations with multiple values').lower()
        max_val = df[cfg['parameter']].mean() + df[cfg['parameter']].std() * 2
        cfg['max_value'] = st.number_input('Maximum Value', max_val)
        if cfg['prop_size_method'] == 'size':
            cfg['max_prop_size'] = st.number_input('Maximum radius', cfg['max_prop_size'])
            cfg['min_prop_size'] = st.number_input('Minimum radius', cfg['min_prop_size'])
        else:
            cfg['lin_palette'] = st.selectbox('Color Palette', helper.bokeh_palettes((256)))
            cfg['symbol_size'] = st.number_input('Symbol size', min_value=1, max_value = 50, value=cfg['symbol_size'])
        cfg['fill_alpha'] = st.number_input('Fill alpha', min_value=0.1, max_value = 1.0, step=0.1, value=cfg['fill_alpha'])
        
    return cfg

def show_locations_map():
    df = show_filter(st.session_state.config.row_sample_df,['station','date'])
    cfg = get_location_map_cfg()
    map = Map(df, cfg)
    p = map.get_map()
    st.bokeh_chart(p)
    helper.show_save_file_button(p)

def show_parameters_map():
    cfg = cn.map_cfg
    cfg['parameter'] = helper.select_parameter(sidebar_flag=True)
    df = show_filter(st.session_state.config.row_sample_df,['station','date'])
    cfg = get_parameter_map_cfg(cfg, df)
    map = Map(df, cfg)
    p = map.get_plot()

    dic = {'min': 'minimum', 'max': 'maximum', 'mean': 'mean' }
    st.markdown(f"**{cfg['parameter']}, {dic[cfg['aggregation']]} value for each station.**")
    st.bokeh_chart(p)
    helper.show_save_file_button(p)

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    
    if menu_action == menu_options[0]:
        show_locations_map()
    elif menu_action == menu_options[1]:
        show_parameters_map()
        
    
