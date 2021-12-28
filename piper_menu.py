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

image_file_format = 'png'
group_by_options = [None, 'Station']
legend_options = [None, 'Station']

def get_cfg(cfg: dict, df: pd.DataFrame):
    with st.sidebar.expander("⚙️ Settings"):
        cfg['group_plot_by'] = st.selectbox('Group plots by', group_by_options)
        cfg['group_legend_by'] = st.selectbox('Legend', legend_options)
        cfg['symbol_size'] = st.number_input('Marker size', min_value=1, max_value=50, step=1, value=int(cfg['symbol_size']))
        cfg['fill_alpha'] = st.number_input('Marker alpha', min_value=0.0,max_value=1.0,step=0.1, value=cfg['fill_alpha'])
        cfg['plot_width'] = st.number_input('Plot width', cfg['plot_width'])
    return cfg

def show_filter(df: pd.DataFrame):
    with st.sidebar.expander("🔎 Filter"):
        station_options = st.session_state.config.get_station_list()
        sel_stations = st.multiselect("Stations", station_options)
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

def show_piper_plot():
    cfg = cn.piper_cfg
    df = st.session_state.config.row_sample_df
    cfg = get_cfg(cfg, df)
    df = show_filter(df)
    piper = Piper(df, cfg)
    p = piper.get_plot()
    st.bokeh_chart(p)
    #helper.show_save_file_button(p, 'key1')

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    
    if menu_action == menu_options[0]:
        show_piper_plot()