import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from bokeh.core.enums import MarkerType, LineDash

from boxplot import Boxplot
import helper
import const as cn
from helper import get_language, flash_text, bokeh_palettes, show_save_file_button


lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.config.language)


def get_parameters(df:pd.DataFrame):
    parameter_options = list(st.session_state.config._parameter_map_df.index)
    parameter_options.sort()
    x_par = st.sidebar.selectbox(label=lang['x_parameter'], options=parameter_options, index=0)
    y_par = st.sidebar.selectbox(label=lang['y_parameter'], options=parameter_options, index=1)
    return x_par, y_par


def get_filter(df:pd.DataFrame):
    with st.sidebar.expander(lang['filter']):
        lst_stations = list(df[st.session_state.config.station_col].unique())
        sel_stations = st.multiselect(label=lang['station'], options=lst_stations)
    
    if len(sel_stations)> 0:
        df = df[df[st.session_state.config.station_col].isin(sel_stations)]
    else:
        sel_stations = lst_stations
    return df, sel_stations


def get_boxes(cfg):
    result = []
    group_options = []

    if cfg['box_group_variable'].lower() == 'parameter':
        group_options = list(st.session_state.config.parameter_map_df.index)
        def_values = group_options[:5]
        result = st.multiselect(label=lang['parameters'], options=group_options, default=def_values)
    elif cfg['box_group_variable'].lower() == 'station':
        group_options = st.session_state.config.get_station_list()
        def_values = group_options[:5]
        result = st.sidebar.multiselect(label=cfg['box_group_variable'], options=group_options, default=def_values)
    
    elif cfg['box_group_variable'].lower() == 'year':
        group_options = helper.get_distinct_values(st.session_state.config.self._row_sample_df, 'year')
        def_values = group_options[:5]
        result = st.multiselect(label=cfg['box_group_variable'], options=group_options, default=def_values)
    return result


def  get_parameter(cfg):
    group_options = list(st.session_state.config.parameter_map_df.index)
    result = st.sidebar.selectbox(label=lang['parameter'], options=group_options, index=0)
    return result

def get_group_parameter(cfg):
    result = []
    result = st.sidebar.selectbox(label=lang['group_by_options_label'], options=lang['group_by_options'], index=0)
    return result

def show_box_plot():
    def get_settings(cfg, data):
        # field used to aggregate values for boxes 
        cfg['box_group_parameter'] = get_group_parameter(cfg)
        # selection of values to be shown as boxes 
        cfg['box_group_values'] = get_boxes(cfg)
        if cfg['box_group_parameter'].lower() != 'parameter':
            cfg['y_parameter'] = get_parameter(cfg)

        with st.sidebar.expander(lang['settings']):
            cfg['y_auto'] = st.checkbox(label=lang['y_auto'], value=True)
            if not cfg['y_auto']:
                cols = st.columns(2)
                with cols[0]:
                    cfg['y_axis_min'] = st.text_input(label=lang['y_axis_min'], value = cfg['y_axis_min'] )
                with cols[1]:
                    cfg['y_axis_max'] = st.text_input(label=lang['y_axis_max'], value = cfg['y_axis_max'] )
        return cfg

    data = st.session_state.config.row_value_df
    cfg = cn.boxplot_cfg
    data, sel_stations = get_filter(data)
    cfg = get_settings(cfg, data)
    data = data[(data[st.session_state.config.station_col].isin(cfg['box_group_values'])) & (data[st.session_state.config.parameter_col] == cfg['y_parameter'])]
    data = data[[st.session_state.config.station_col, st.session_state.config.value_col]]
    data.columns =  ['group','score']

    boxplot = Boxplot(data, cfg)
    plot = boxplot.get_plot()
    st.bokeh_chart(plot)
    
def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)

    if menu_action == MENU_OPTIONS[0]:
        show_box_plot()
    elif menu_action == MENU_OPTIONS[1]:
        pass # correlation matrix to come