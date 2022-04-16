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
    
    lang = helper.get_language(__name__, st.session_state.language)
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
        station_options = st.session_state.get_station_list()
        sel_stations = st.multiselect(label=lang['stations'], options=station_options)
        if len(sel_stations)>0:
            df = df[(df[st.session_state.station_col].isin(sel_stations)) & (df['alk_pct'] > 0)]
        #if st.session_state.col_is_mapped(cn.SAMPLE_DATE_COL):
        #    date_col = st.session_state.key2col()[cn.SAMPLE_DATE_COL]
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
    x, unmatched_cat = st.session_state.project.master_par_id_2_par_id([cn.BICARBONATE_ID])
    prj=st.session_state.project
    cfg['alk_source'] = 2 #1 use hco3, 2: use HCO3 + CO3
    cfg['na_k'] = 1  # use Na+K
    if cfg['alk_source']==1: # use hco3, co3
        anions, unmatched = prj.master_par_id_2_par_id([cn.BICARBONATE_ID, cn.CARBONATE_ID, cn.CHLORID_ID, cn.SULFATE_ID])
    elif cfg['alk_source']==2: # use alk, remove hco3, co3
        anions, unmatched = prj.master_par_id_2_par_id([cn.ALKALINITY_ID, cn.CHLORID_ID, cn.SULFATE_ID])
            
    if cfg['na_k']==0:
        cations, unmatched = prj.master_par_id_2_par_id([cn.CALCIUM_ID, cn.SODIUM_ID, cn.MAGNESIUM_ID])
    else:
        cations, unmatched = prj.master_par_id_2_par_id([cn.CALCIUM_ID, cn.SODIUM_ID, cn.POTASSIUM_ID, cn.MAGNESIUM_ID])
    
    # remove not matching parameters
    data = st.session_state.project.get_observations(cations + anions, cfg['stations'])
    data = pd.pivot_table(data,
        values='numeric_value',
        index=['station_key','station_id', 'sampling_date'],
        columns='parameter_id',
        aggfunc=np.max
    ).reset_index()
    data = data[(data[prj.par_id(cn.CALCIUM_ID)] > 0) & (data[prj.par_id(cn.SODIUM_ID)] > 0) & (data[prj.par_id(cn.ALKALINITY_ID)] > 0)]

    # convert major ions to meq/L
    x = st.session_state.project.parameters_df
    major_ions = st.session_state.project.get_parameter_name_list(cations + anions, 'short_name_en')
    meqpl_ions = [f"{item}_meqpl" for item in major_ions]
    data = helper.add_meqpl_columns(data, cations + anions, meqpl_ions)
    if cfg['na_k'] == 1:
        data['Na_meqpl'] = data['Na_meqpl'] + data['K_meqpl']
        data = data.drop(columns='K_meqpl', axis=1)
        cations.pop(2)

    cations_names = st.session_state.project.get_parameter_name_list(cations, 'short_name_en')
    meqpl_cations = [f"{item}_meqpl" for item in cations_names]
    anions_names = st.session_state.project.get_parameter_name_list(anions, 'short_name_en')
    meqpl_anions = [f"{item}_meqpl" for item in anions_names]

    #calculate meq% for anions and cations seperately
    pct_cations = [f"{item}_pct" for item in cations_names]
    pct_anions = [f"{item}_pct" for item in anions_names]
    
    data = helper.add_pct_columns(data, meqpl_cations, pct_cations, sum_col='sum_cations_meqpl')
    data = helper.add_pct_columns(data, meqpl_anions, pct_anions, sum_col='sum_anions_meqpl')
    return data, pct_cations, pct_anions


def show_piper_plot():
    cfg= st.session_state.user.read_config(cn.PIPER_ID, 'default')
    cfg['stations'] = helper.get_stations(default=cfg['stations'], filter="")
    data, cfg['cation_cols'], cfg['anion_cols'] = get_data(cfg)
    cfg = get_cfg(cfg, data)
    
    piper = Piper(data, cfg)
    p = piper.get_plot()
    st.bokeh_chart(p)
    #helper.show_save_file_button(p, 'key1')
    st.session_state.user.save_config(cn.PIPER_ID, 'default', cfg)

def show_menu():
    set_lang()
    menu_options = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=menu_options)
    
    if menu_action == menu_options[0]:
        show_piper_plot()