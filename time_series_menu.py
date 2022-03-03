from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.core.enums import MarkerType, LineDash

import const as cn
from time_series import Time_series
import helper


lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


def show_time_series_multi_parameters():

    def show_settings(cfg, data)->dict:
        with st.sidebar.expander(lang['settings']):
            cfg['time_axis_auto'] = st.checkbox(label=lang['time_axis_auto'], value=True)
            if not cfg['time_axis_auto']:
                if cfg['time_axis_start'] == 0:
                    cfg['time_axis_start'] = data['sampling_date'].min()
                    cfg['time_axis_end'] = data['sampling_date'].max()
                cfg['time_axis_start'] = st.date_input(label=lang['time_axis_min'],value=cfg['time_axis_start'] )
                cfg['time_axis_end'] = st.date_input(label=lang['time_axis_max'],value=cfg['time_axis_end'])

            cfg['y_axis_auto'] = st.checkbox(label=lang['y_axis_auto'], value = True)
            if not cfg['y_axis_auto']:
                cfg['y_axis_start'] = st.number_input(label=lang["y_axis_min"], value=cfg['y_axis_start'])
                cfg['y_axis_end'] = st.number_input(label=lang["y_axis_max"], value=cfg['y_axis_end'])
            palette_options = helper.bokeh_palettes(10)
            cfg['palette'] = st.selectbox(label=lang["color_palette"], options=palette_options)
        return cfg

    cfg= st.session_state.config.user.read_config(cn.TIME_SERIES_ID,'default')
    cfg['parameters'] = helper.get_parameters(default=cfg['parameters'], filter="")
    cfg['stations'] = helper.get_stations(default=cfg['stations'],filter="")
    data = st.session_state.config.project.get_observations(cfg['parameters'], cfg['stations'])
    if len(data)>0:
        cfg = show_settings(cfg, data)
        param_dict=st.session_state.config.project.get_parameter_dict()
        cfg['legend_items'] = [*map(param_dict.get, cfg['parameters'])] 
        cfg['legend_col'] = 'parameter'
        if cfg['stations'] == []:
            stations = list(data['station_id'])
        else: 
            stations = cfg['stations']
        station_dict=st.session_state.config.project.get_station_list()
        for station in stations:
            station_data = data[data['station_id'] == station].sort_values('sampling_date')
            cfg['plot_title'] = station_dict[station]
            plot = Time_series(station_data, cfg).get_plot()
            st.bokeh_chart(plot)
            helper.show_save_file_button(plot, station)
    st.session_state.config.user.save_config(cn.TIME_SERIES_ID, 'default', cfg)


def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options_timeseries"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        show_time_series_multi_parameters()

