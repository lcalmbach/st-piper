import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

from plots.histogram import Histogram
from plots.map import Map
import helper
import const as cn


lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


def show_filter(df: pd.DataFrame, filters:tuple):
    def filter_station(df):
        station_col = st.session_state.key2col()[cn.STATION_IDENTIFIER_COL]
        station_options = st.session_state.get_station_list()
        sel_stations = st.multiselect(label=lang['stations'], options=station_options)
        if len(sel_stations)>0:
            df = df[df[station_col].isin(sel_stations)]
        return df, sel_stations
    
    def filter_date(df):
        date_col = st.session_state.key2col()[cn.SAMPLE_DATE_COL]
        df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        min_date = df[date_col].min().to_pydatetime().date()
        max_date = df[date_col].max().to_pydatetime().date()
        
        from_date = st.sidebar.date_input(label=lang['from_date'], value=min_date)
        to_date = st.sidebar.date_input(label=lang['to_date'], value=max_date)
        if (from_date != min_date) or (to_date != max_date):
            df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]
        return df, min_date, max_date
    
    def filter_year(df):
        date_col = st.session_state.key2col()[cn.SAMPLE_DATE_COL]
        df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        min_year = df[date_col].min().to_pydatetime().year
        max_year = df[date_col].max().to_pydatetime().year
        
        sel_from_year = st.number_input(label=lang['from_year'], value=min_year, min_value=min_year, max_value=max_year)
        sel_to_year = st.number_input(label=lang['to_year'], value = max_year, min_value=min_year, max_value=max_year)
        if (sel_from_year != min_year) or (sel_to_year != max_year):
            df = df[(df[date_col].dt.year >= sel_from_year) & (df[date_col].dt.year < sel_to_year)]
        return df, sel_from_year, sel_to_year

    with st.sidebar.expander(lang['filter']):
        if lang['station'] in filters:
            df, sel_stations = filter_station(df)
        if lang['date'] in filters:
            df, min_date, max_date = filter_date(df)
        if lang['year'] in filters:
            df, min_year, max_year = filter_year(df)

        return df

def get_unit(df):
    unit=''
    if st.session_state.col_is_mapped(cn.UNIT_COL):
        unit_col = st.session_state.key2col()[cn.UNIT_COL]
        unit = df.iloc[0][unit_col]
    return unit


def get_config(df, cfg):
    # todo!
    x_min = df['value_numeric'].min()
    x_max = df['value_numeric'].max()
    
    with st.sidebar.expander(lang['settings']):
        cols = st.columns(2)
        with cols[0]:
            cfg['x_min'] = float(st.text_input(label=lang['x_start'], value=x_min))
            
        with cols[1]:
            cfg['x_max'] = float(st.text_input(label=lang['x_end'], value=x_max))

        unit = 'mg/L' #st.session_state.project.
        cfg['x_axis_title'] = f"{cfg['parameter']} ({unit})" if unit > '' else cfg['parameter']
        cfg['x_axis_title'] = st.text_input(label=lang['x_title'], value=cfg['x_axis_title'])
        cfg['y_axis_title'] = st.text_input(label=lang['y_title'], value=cfg['y_axis_title'])
        cfg['bins'] = st.number_input(label=lang['bins'], value=int(cfg['bins']), min_value=2, max_value=1000, step=1)
        cfg['fill_color']=st.color_picker(label=lang['fill_color'], value=cfg['fill_color'])
        cfg = cfg
    return cfg


def get_parameter():
    parameter_options = st.session_state.parameter_map_df.index
    result = st.sidebar.selectbox(label=lang['parameter'], options=parameter_options)
    return result


def show_histogram(df:pd.DataFrame, cfg:dict):
    histo = Histogram(df, cfg)
    p = histo.get_plot()
    st.bokeh_chart(p)


def show_menu():
    set_lang()
    menu_options = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=menu_options)
    
    if menu_action == menu_options[0]:
        cfg= st.session_state.user.read_config(cn.HISTOGRAM_ID,'default')

        cfg['stations'] = helper.get_stations(default=cfg['stations'],filter="")
        cfg['parameter'] = helper.get_parameter(default=cfg['parameter'], label='Parameter', filter='')
        
        filters = (lang['station'], lang['year'])
        # df = show_filter(df, filters)
        data = st.session_state.project.get_observations(filter_parameters=[cfg['parameter']], filter_stations=cfg['stations'])
        cfg = get_config(data, cfg)
        show_histogram(data, cfg)
        st.session_state.user.save_config(cn.HISTOGRAM_ID, 'default', cfg)

