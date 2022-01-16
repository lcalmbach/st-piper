import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from bokeh.core.enums import MarkerType, LineDash

from schoeller import Schoeller
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


def show_schoeller_plot():
    def get_settings(cfg, data):
        with st.sidebar.expander(lang['settings']):
            cfg['group_plot_by'] = st.selectbox(label=lang['group_plots_by'], options=lang['group_by_options'])
            cfg['group_legend_by'] = st.selectbox(label=lang['legend'], options=lang['legend_options'])
            cfg['show_symbols'] = st.checkbox(label=lang['show_symbols'], value=True)

            cfg['y_auto'] = st.checkbox(label=lang['y_auto'], value=True)
            if not cfg['y_auto']:
                cols = st.columns(2)
                with cols[0]:
                    cfg['y_axis_min'] = st.text_input(label=lang['y_axis_min'], value = cfg['y_axis_min'] )
                with cols[1]:
                    cfg['y_axis_max'] = st.text_input(label=lang['y_axis_max'], value = cfg['y_axis_max'] )
        return cfg

    data = st.session_state.config.row_sample_df
    cfg = cn.schoeller_cfg
    data, sel_stations = get_filter(data)
    cfg = get_settings(cfg, data)
    if cfg['group_plot_by'] == lang['group_by_options'][0]: #None
        schoeller = Schoeller(data, cfg)
        plot = schoeller.get_plot()
        st.bokeh_chart(plot)
    else:
        if len(sel_stations) == 0:
            sel_stations = data[st.session_state.config.station_col].unique()
        for station in sel_stations:
            df = data[data[st.session_state.config.station_col] == station]
            if len(df)>0:
                cfg['plot_title'] = station
                schoeller = Schoeller(df, cfg)
                plot, df_stats = schoeller.get_plot()
                st.bokeh_chart(plot)
            else:
                st.info(lang['no_record_found_4station'].format(station))

def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)

    if menu_action == MENU_OPTIONS[0]:
        show_schoeller_plot()
    elif menu_action == MENU_OPTIONS[1]:
        pass # correlation matrix to come