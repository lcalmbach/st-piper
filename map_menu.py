from os import startfile
from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
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

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


def show_filter(df: pd.DataFrame, filters: list, cfg: dict):
    with st.sidebar.expander(f"🔎 {lang['filter']}"):
        if lang['station'].lower() in filters:
            station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
            station_options = st.session_state.config.get_station_list()
            sel_stations = st.multiselect(label=lang['stations'], options=station_options)
            if len(sel_stations)>0:
                df = df[df[station_col].isin(sel_stations)]
        
        if lang['date'].lower() in filters and st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
            date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
            df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
            min_date = df[date_col].min().to_pydatetime().date()
            max_date = df[date_col].max().to_pydatetime().date()
            
            from_date = st.date_input(label=lang['from_date'], value=min_date)
            to_date = st.date_input(label=lang['to_date'], value=max_date)
            if (from_date != min_date) or (to_date != max_date):
                df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]

        if lang['value'].lower() in  filters:
            cols = st.columns((2,3))
            with cols[0]:
                operator = st.selectbox(cfg['parameter'], [None] + cn.COMPARE_OPTIONS)
            with cols[1]:
                compare_value = float(st.text_input(label=lang['value'], value='0'))
            if operator != None:
                if operator == '>':
                    df = df[df[st.session_state.config.value_col] > compare_value]
                elif operator == '<':
                    df = df[df[st.session_state.config.value_col] < compare_value]
                elif operator == '=':
                    df = df[df[st.session_state.config.value_col] == compare_value]
                elif operator == '>=':
                    df = df[df[st.session_state.config.value_col] >= compare_value]
                elif operator == '<=':
                    df = df[df[st.session_state.config.value_col] <= compare_value]

    return df

def get_location_map_cfg():
    return cn.map_cfg

def get_parameter_map_cfg(cfg, df):
    with st.sidebar.expander(f"⚙️ {lang['settings']}"):
        lst_options = [lang['color'], lang['size']]
        cfg['prop_size_method'] = st.radio(labal=lang['prop_color_size'], options=lst_options).lower()
        lst_stat_functions=[lang['min'], lang['max'], lang['mean']]
        cfg['aggregation'] = st.radio(label=lang['aggregation'], options=lst_stat_functions, help=lang['aggregation_station_help']).lower()
        max_val = df[st.session_state.config.value_col].mean() + df[st.session_state.config.value_col].std() * 2
        cfg['max_value'] = st.number_input(label=lang['max_value'] , value=max_val)
        if cfg['prop_size_method'] == lang['size'].lower():
            cfg['max_prop_size'] = st.number_input(label=lang['max_radius'], value=cfg['max_prop_size'])
            cfg['min_prop_size'] = st.number_input(label=lang['min_radius'], value=cfg['min_prop_size'])
        else:
            cfg['lin_palette'] = st.selectbox(label=lang['min_radius'], options=helper.bokeh_palettes((256)))
            cfg['symbol_size'] = st.number_input(label=lang['symbol_size'], min_value=1, max_value=50, value=int(cfg['symbol_size']))
        cfg['fill_alpha'] = st.number_input(label=lang['fill_alpha'], min_value=0.1, max_value = 1.0, step=0.1, value=float(cfg['fill_alpha']))
        
    return cfg

def show_locations_map():
    cfg = get_location_map_cfg()
    filter_fields = [lang['station'], lang['date']]
    df = show_filter(st.session_state.config.row_sample_df,filter_fields, cfg)
    map = Map(df, cfg)
    p = map.get_plot()
    st.bokeh_chart(p)
    helper.show_save_file_button(p, 'key1')

def show_parameters_map():
    cfg = cn.map_cfg
    cfg['parameter'] = helper.select_parameter(sidebar_flag=True)
    df = st.session_state.config.row_value_df
    df = df[df[st.session_state.config.parameter_col] == cfg['parameter']]
    filter_fields = ['station','date', 'value']
    df = show_filter(df,filter_fields, cfg)
    cfg = get_parameter_map_cfg(cfg, df)
    map = Map(df, cfg)
    p = map.get_plot()

    dic = {'min': lang['min'], 'max': lang['max'], 'mean': lang['mean'] }
    st.markdown(f"**{cfg['parameter']}, {dic[cfg['aggregation']]} value for each station.**")
    st.bokeh_chart(p)
    #helper.show_save_file_button(p, 'key1')

def show_menu():
    set_lang()
    menu_options = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=menu_options)
    
    if menu_action == menu_options[0]:
        show_locations_map()
    elif menu_action == menu_options[1]:
        show_parameters_map()
        
    

