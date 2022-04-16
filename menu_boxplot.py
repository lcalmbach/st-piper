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
    lang = get_language(__name__, st.session_state.language)


def get_parameters(df:pd.DataFrame):
    parameter_options = list(st.session_state._parameter_map_df.index)
    parameter_options.sort()
    x_par = st.sidebar.selectbox(label=lang['x_parameter'], options=parameter_options, index=0)
    y_par = st.sidebar.selectbox(label=lang['y_parameter'], options=parameter_options, index=1)
    return x_par, y_par


def get_filter(df:pd.DataFrame):
    with st.sidebar.expander(lang['filter']):
        lst_stations = list(df[st.session_state.station_col].unique())
        sel_stations = st.multiselect(label=lang['station'], options=lst_stations)
    
    if len(sel_stations)> 0:
        df = df[df[st.session_state.station_col].isin(sel_stations)]
    else:
        sel_stations = lst_stations
    return df, sel_stations


def get_boxes(cfg):
    result = []
    group_options = []

    if cfg['box_group_variable'].lower() == 'parameter':
        group_options = list(st.session_state.parameter_map_df.index)
        def_values = group_options[:5]
        result = st.multiselect(label=lang['parameters'], options=group_options, default=def_values)
    elif cfg['box_group_variable'].lower() == 'station':
        result = helper.get_stations(default=cfg['box_group_values'], filter="")
    
    elif cfg['box_group_variable'].lower() == 'year':
        group_options = helper.get_distinct_values(st.session_state.self._row_sample_df, 'year')
        def_values = group_options[:5]
        result = st.multiselect(label=cfg['box_group_values'], options=group_options, default=def_values)
    return result


def  get_parameter(cfg):
    group_options = list(st.session_state.parameter_map_df.index)
    result = st.sidebar.selectbox(label=lang['parameter'], options=group_options, index=0)
    return result

def get_group_parameter(cfg):
    result = []
    result = st.sidebar.selectbox(label=lang['group_by_options_label'], options=lang['group_by_options'], index=0)
    return result

def show_box_plot():
    def get_settings(cfg, data):
        # field used to aggregate values for boxes 
        
        with st.sidebar.expander(lang['settings']):
            cfg['y_auto'] = st.checkbox(label=lang['y_auto'], value=True)
            if not cfg['y_auto']:
                cols = st.columns(2)
                with cols[0]:
                    cfg['y_axis_min'] = st.text_input(label=lang['y_axis_min'], value = cfg['y_axis_min'] )
                with cols[1]:
                    cfg['y_axis_max'] = st.text_input(label=lang['y_axis_max'], value = cfg['y_axis_max'] )
        return cfg

    cfg = st.session_state.user.read_config(cn.BOXPLOT_ID, 'default')
    cfg['y_parameter'] = helper.get_parameter(cfg['y_parameter'], label='Parameter', filter='')
    cfg['stations'] = helper.get_stations(default=[], filter="")
    data = st.session_state.project.get_observations([cfg['y_parameter']], cfg['stations'])

    data = data[['station_key', 'numeric_value']]
    data.columns =  ['group','score']
    cfg = get_settings(cfg, data)
    boxplot = Boxplot(data, cfg)
    plot = boxplot.get_plot()
    st.bokeh_chart(plot)
    st.session_state.user.save_config(cn.BOXPLOT_ID, 'default', cfg)

def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)

    if menu_action == MENU_OPTIONS[0]:
        show_box_plot()
    elif menu_action == MENU_OPTIONS[1]:
        pass # correlation matrix to come