import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

from histogram import Histogram
import helper
import const as cn
from map import Map


def show_filter(df: pd.DataFrame, filters:tuple):
    def filter_station(df):
        station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
        station_options = st.session_state.config.get_station_list()
        sel_stations = st.multiselect("Stations", station_options)
        if len(sel_stations)>0:
            df = df[df[station_col].isin(sel_stations)]
        return df, sel_stations
    
    def filter_date(df):
        date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
        df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        min_date = df[date_col].min().to_pydatetime().date()
        max_date = df[date_col].max().to_pydatetime().date()
        
        from_date = st.sidebar.date_input("From date", min_date)
        to_date = st.sidebar.date_input("From date", max_date)
        if (from_date != min_date) or (to_date != max_date):
            df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]
        return df, min_date, max_date
    
    def filter_year(df):
        date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
        df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        min_year = df[date_col].min().to_pydatetime().year
        max_year = df[date_col].max().to_pydatetime().year
        
        sel_from_year = st.number_input("From year", value=min_year, min_value=min_year, max_value=max_year)
        sel_to_year = st.number_input("to year", value = max_year, min_value=min_year, max_value=max_year)
        if (sel_from_year != min_year) or (sel_to_year != max_year):
            df = df[(df[date_col].dt.year >= sel_from_year) & (df[date_col].dt.year < sel_to_year)]
        return df, sel_from_year, sel_to_year

    with st.sidebar.expander("🔎 Filter"):
        if 'station' in filters:
            df, sel_stations = filter_station(df)
        if 'date' in filters:
            df, min_date, max_date = filter_date(df)
        if 'year' in filters:
            df, min_year, max_year = filter_year(df)

        return df

def get_unit(df):
    unit=''
    if st.session_state.config.col_is_mapped(cn.UNIT_COL):
        unit_col = st.session_state.config.key2col()[cn.UNIT_COL]
        unit = df.iloc[0][unit_col]
    return unit

def get_config(df, par):
    cfg = cn.histogram_cfg

    cfg['par'] = par
    cfg['value_col'] = st.session_state.config.key2col()[cn.VALUE_NUM_COL]
    x_min = df[cfg['value_col']].min()
    x_max = df[cfg['value_col']].max()
    
    with st.sidebar.expander("⚙️ Settings"):
        cols = st.columns(2)
        with cols[0]:
            cfg['x_min'] = float(st.text_input("X-axis start", value=x_min))
            
            
        with cols[1]:
            cfg['x_max'] = float(st.text_input("X-axis end", value=x_max))
            
        unit = get_unit(df)
        cfg['x_axis_title'] = f"{par} ({unit})" if unit > '' else par
        cfg['x_axis_title'] = st.text_input("X-axis title", cfg['x_axis_title'])
        cfg['y_axis_title'] = st.text_input("Y-axis title", cfg['y_axis_title'])
        cfg['bins'] = st.number_input("Bins", value=cfg['bins'], min_value=0, max_value=1000, step=1)
        cfg['colors'][0]=st.color_picker('Fill color', value=cfg['colors'][0])
        cfg = cfg
    return cfg

def get_parameter():
    parameter_options = st.session_state.config.parameter_map_df.index
    result = st.sidebar.selectbox('Parameter', parameter_options)
    return result

def show_histogram(df:pd.DataFrame, cfg:dict):
    histo = Histogram(df, cfg)
    p = histo.get_plot()
    st.bokeh_chart(p)
    helper.show_save_file_button(p)

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    
    df = st.session_state.config.row_value_df
    
    if menu_action == menu_options[0]:
        par = get_parameter()
        par_col = st.session_state.config.key2col()[cn.PARAMETER_COL]
        df = df[df[par_col] == par]
        cfg = get_config(df, par)
        filters = ('station', 'year')
        df = show_filter(df, filters)
        
        show_histogram(df, cfg)
