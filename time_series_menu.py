from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.core.enums import MarkerType, LineDash

import const as cn
from time_series import Time_series
from helper import get_language, flash_text, bokeh_palettes, show_save_file_button


lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.config.language)


def show_time_series_multi_parameters():
    def get_filter(df):
        parameter_options = list(st.session_state.config.parameter_map_df.index)
        parameter_options.sort()
        sel_parameters = st.sidebar.multiselect(label=lang['parameter'], options=parameter_options, default=parameter_options[0])
        x = st.session_state.config.key2col()
        station_col = x[cn.STATION_IDENTIFIER_COL]
        par_col = x[cn.PARAMETER_COL]
        value_col = x[cn.VALUE_NUM_COL]
        date_col = x[cn.SAMPLE_DATE_COL]
        lst_stations = list(df[station_col].unique())
        sel_stations = st.sidebar.multiselect(label=lang['station'], options=lst_stations, default=lst_stations[0])
        return sel_parameters, sel_stations, station_col, date_col, par_col, value_col

    def show_settings()->dict:
        cfg= cn.time_series_cfg
        with st.sidebar.expander(lang['settings']):
            cfg['x_axis_auto'] = st.checkbox(label=lang['time_axis_auto'], value=True)
            if not cfg['x_axis_auto']:
                cfg['time_axis_start'] = st.date_input(label=lang['time_axis_start'], value=cfg['time_axis_start'])
                cfg['time_axis_end'] = st.date_input(label=lang['time_axis_end'], value=cfg['time_axis_end'])

            cfg['y_axis_auto'] = st.checkbox(label=lang['y_axis_auto'], value = True)
            if not cfg['y_axis_auto']:
                cfg['y_axis'] = st.number_input(label=lang["y_axis_max"], value=cfg['y_axis'])
            palette_options = bokeh_palettes(10)
            cfg['palette'] = st.selectbox(label=lang["color_palette"], options=palette_options)
        return cfg

    data = st.session_state.config.row_value_df
    sel_parameters, sel_stations, station_col, date_col, par_col, value_col = get_filter(data)
    cfg = show_settings()
    cfg['legend_items'] = sel_parameters
    cfg['legend_col'] = st.session_state.config.parameter_col
    data = data[data[cfg['legend_col']].isin(sel_parameters)]
    if sel_stations == []:
        sel_stations = list(data[st.session_state.config.station_col].unique())
        sel_stations.sort
    for station in sel_stations:
        station_data = data[data[station_col] == station].sort_values(date_col)
        cfg['plot_title'] = station
        plot = Time_series(station_data, cfg).get_plot()
        st.bokeh_chart(plot)
        show_save_file_button(plot, station)


def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options_timeseries"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        show_time_series_multi_parameters()

