import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from bokeh.core.enums import MarkerType, LineDash

from plots.scatter import Scatter
import helper
import const as cn
from helper import get_language, flash_text, bokeh_palettes, show_save_file_button


lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


def get_filter(df:pd.DataFrame):
    with st.sidebar.expander(lang['filter']):
        lst_stations = list(df[st.session_state.station_col].unique())
        sel_stations = st.multiselect(label=lang['station'], options=lst_stations)
    
    if len(sel_stations)> 0:
        df = df[df[st.session_state.station_col].isin(sel_stations)]
    else:
        sel_stations = lst_stations
    return df, sel_stations


def get_settings(cfg, data):
    with st.sidebar.expander(lang['settings']):
        cfg['group_plot_by'] = st.selectbox(label=lang['group_plots_by'], options=lang['group_by_options'])
        cfg['group_legend_by'] = st.selectbox(label=lang['legend'], options=lang['legend_options'])
        cfg['symbol_size'] = st.number_input(label=lang['marker_size'], min_value=1, max_value=50, step=1, value=int(cfg['symbol_size']))
        cfg['fill_alpha'] = st.number_input(label=lang['marker_alpha'], min_value=0.0,max_value=1.0,step=0.1, value=cfg['fill_alpha'])

        cfg['axis_auto'] = st.checkbox(label=lang['axis_auto'], value=True)
        if not cfg['axis_auto']:
            cols = st.columns(2)
            with cols[0]:
                cfg['x_axis_min'] = st.text_input(label=lang['x_axis_min'])
                cfg['y_axis_min'] = st.text_input(label=lang['y_axis_min'])
            with cols[1]:
                cfg['x_axis_max'] = st.text_input(label=lang['x_axis_max'])
                cfg['y_axis_max'] = st.text_input(label=lang['y_axis_max'])
        
        cfg['show_h_line'] = st.checkbox(label=lang['show_h_line'], value=False)
        if cfg['show_h_line']:
            cfg['h_line_intercept'] = st.number_input(label=lang['h_line_intercept'], value=cfg['h_line_intercept'])
            cfg['h_line_pattern'] = st.selectbox(label=lang['h_line_pattern'], 
                                    options=list(LineDash), 
                                    index=list(LineDash).index(cfg['h_line_pattern']))
            cfg['h_line_color'] = st.color_picker(label=lang['h_line_color'], value=cfg['h_line_color'])

        cfg['show_v_line'] = st.checkbox(label=lang['show_v_line'], value=False)
        if cfg['show_v_line']:
            cfg['v_line_intercept'] = st.number_input(label=lang['v_line_intercept'], value=0)
            cfg['v_line_pattern'] = st.selectbox(label=lang['v_line_pattern'], 
                                    options=list(LineDash), 
                                    index=list(LineDash).index(cfg['v_line_pattern']))
            cfg['v_line_color'] = st.color_picker(label=lang['v_line_color'], value=cfg['v_line_color'])
        cfg['show_corr_line'] = st.checkbox(label=lang['show_corr_line'], value=False)
        if cfg['show_corr_line']:
            cfg['corr_line_pattern'] = st.selectbox(label=lang['corr_line_pattern'], 
                                    options=list(LineDash), 
                                    index=list(LineDash).index(cfg['corr_line_pattern']))
            cfg['corr_line_color'] = st.color_picker(label=lang['corr_line_color'], value=cfg['corr_line_color'])
    return cfg


def show_scatter_plot():
    cfg= st.session_state.user.read_config(cn.SCATTER_ID, 'default')
    cfg['stations'] = helper.get_stations(default=cfg['stations'], filter="")
    cfg['x_par'] = helper.get_parameter(cfg['x_par'], label='X-Parameter', filter='')
    cfg['y_par'] = helper.get_parameter(cfg['y_par'], label='Y-Parameter', filter='')
    data = st.session_state.project.get_observations([cfg['x_par'], cfg['y_par']], cfg['stations'])
    data = pd.pivot_table(data,
        values='value_numeric',
        index=['station_id', 'sampling_date'],
        columns='parameter_name',
        aggfunc=np.mean
    ).reset_index()
    #data, sel_stations = get_filter(data)
    cfg = get_settings(cfg, data)
    if cfg['group_plot_by'] == lang['group_by_options'][0]:
        scatter = Scatter(data, cfg)
        plot, df_stats = scatter.get_plot()
        st.bokeh_chart(plot)
        if cfg['show_corr_line']:
            with st.expander("Stats"):
                AgGrid(df_stats)
    else:
        if len(sel_stations) == 0:
            sel_stations = data[st.session_state.station_col].unique()
        for station in sel_stations:
            df = data[data[st.session_state.station_col] == station]
            if len(df)>0:
                cfg['plot_title'] = station
                scatter = Scatter(df, cfg)
                plot, df_stats = scatter.get_plot()
                st.bokeh_chart(plot)
                if cfg['show_corr_line']:
                    with st.expander(lang['statistics']):
                        AgGrid(df_stats)
            else:
                st.info(lang['no_record_found_4station'].format(station))
    st.session_state.user.save_config(cn.SCATTER_ID, 'default', cfg)

def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)
    
    if menu_action == MENU_OPTIONS[0]:
        show_scatter_plot()
    elif menu_action == MENU_OPTIONS[1]:
        pass # correlation matrix to come
    

