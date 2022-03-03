from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead
from bokeh.core.enums import MarkerType, LineDash
from streamlit.delta_generator import MAX_DELTA_BYTES
from datetime import datetime, timedelta

import helper
import const as cn
from piper import Piper

lang = {}

group_by_options = []
legend_options = []

def set_lang():
    global group_by_options
    global legend_options
    global lang
    
    lang = helper.get_language(__name__, st.session_state.config.language)
    group_by_options = [None, lang['station']]
    legend_options = [None, lang['station']]


def get_cfg(cfg: dict, df: pd.DataFrame):
    with st.sidebar.expander(lang['settings']):
        cfg['group_plot_by'] = st.selectbox(label=lang['group_plots_by'], options=group_by_options)
        cfg['group_legend_by'] = st.selectbox(label=lang['legend'], options=legend_options)
        cfg['symbol_size'] = st.number_input(label=lang['symbol_size'], min_value=1, max_value=50, step=1, value=int(cfg['symbol_size']))
        cfg['fill_alpha'] = st.number_input(label=lang['symbol_alpha'], min_value=0.0,max_value=1.0,step=0.1, value=cfg['fill_alpha'])
        cfg['plot_width'] = st.number_input(label=lang['plot_width'], value=cfg['plot_width'])
    return cfg

def show_filter(df: pd.DataFrame):
    with st.sidebar.expander(lang['filter']):
        station_options = st.session_state.config.get_station_list()
        sel_stations = st.multiselect(label=lang['stations'], options=station_options)
        if len(sel_stations)>0:
            df = df[(df[st.session_state.config.station_col].isin(sel_stations)) & (df['alk_pct'] > 0)]
        #if st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
        #    date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
        ##    df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        #    min_date = df[date_col].min().to_pydatetime().date()
        #    max_date = df[date_col].max().to_pydatetime().date()
        #    
        #    from_date = st.sidebar.date_input("From date", min_date)
        #    to_date = st.sidebar.date_input("From date", max_date)
        #    if (from_date != min_date) or (to_date != max_date):
        #        df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]
    df = df.reset_index()
    return df

def get_data(cfg):
    cfg['parameters'] = cn.MAJOR_IONS
    
    data = st.session_state.config.project.get_observations(cfg['parameters'], cfg['stations'])
    data = pd.pivot_table(data,
        values='numeric_value',
        index=['station_key','station_id', 'sampling_date'],
        columns='parameter_id',
        aggfunc=np.mean
    ).reset_index()
    columns = st.session_state.config.project.get_parameter_name_list(cn.MAJOR_IONS, 'formula')
    columns = [f"{item}_meqpl" for item in columns]
    data = helper.add_meqpl_columns(data, cn.MAJOR_IONS, columns)


def show_piper_plot():
    cfg= st.session_state.config.user.read_config(cn.PIPER_ID, 'default')
    cfg['stations'] = helper.get_stations(default=cfg['stations'], filter="")
    data = get_data(cfg)
    cfg = get_cfg(cfg, data)
    
    piper = Piper(data, cfg)
    p = piper.get_plot()
    st.bokeh_chart(p)
    #helper.show_save_file_button(p, 'key1')
    st.session_state.config.user.save_config(cn.PIPER_ID, 'default', cfg)

def show_menu():
    set_lang()
    menu_options = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=menu_options)
    
    if menu_action == menu_options[0]:
        show_piper_plot()