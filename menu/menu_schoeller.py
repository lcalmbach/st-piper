import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from bokeh.core.enums import MarkerType, LineDash

from plots.schoeller import Schoeller
import helper
import const as cn
from helper import get_lang, flash_text, bokeh_palettes, show_save_file_button


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
            cfg['show_symbols'] = st.checkbox(label=lang['show_symbols'], value=True)

            cfg['y_auto'] = st.checkbox(label=lang['y_auto'], value=True)
            if not cfg['y_auto']:
                cols = st.columns(2)
                with cols[0]:
                    cfg['y_axis_min'] = st.text_input(label=lang['y_axis_min'], value = cfg['y_axis_min'] )
                with cols[1]:
                    cfg['y_axis_max'] = st.text_input(label=lang['y_axis_max'], value = cfg['y_axis_max'] )
        return cfg

def get_data(cfg):
    prj = st.session_state.project
    parameters = [
                    prj.par_id(cn.CALCIUM_ID), prj.par_id(cn.MAGNESIUM_ID),
                    prj.par_id(cn.SODIUM_ID),prj.par_id(cn.POTASSIUM_ID), 
                    prj.par_id(cn.CHLORID_ID), prj.par_id(cn.SULFATE_ID),
                    prj.par_id(cn.ALKALINITY_ID)
                ]
    data = st.session_state.project.get_observations(parameters, cfg['stations'])
    data = pd.pivot_table(data,
        values='value_numeric',
        index=['station_identifier','station_id', 'sampling_date'],
        columns='parameter_id',
        aggfunc=np.max
    ).reset_index()
    #data = data.rename(columns={prj.par_id(cn.CALCIUM_ID): 'Ca++', 
    #                    prj.par_id(cn.MAGNESIUM_ID): 'Mg++',
    #                    prj.par_id(cn.SODIUM_ID): 'Na+',
    #                    prj.par_id(cn.POTASSIUM_ID): 'K+',
    #                    prj.par_id(cn.ALKALINITY_ID): 'Alk',
    #                    prj.par_id(cn.SULFATE_ID): 'SO4--',
    #                    prj.par_id(cn.CHLORID_ID): 'Cl-',
    #                })
    columns = ['Ca++','Mg++','Na+','K+','Alk','SO4--','Cl-']
    data = helper.add_meqpl_columns(data,parameters,columns)
    return data, columns

def show_schoeller_plot():
    cfg= st.session_state.user.read_config(cn.SCHOELLER_ID,'default')
    cfg['stations'] = helper.get_stations(default=cfg['stations'], filter="")
    data, cfg['parameter_names'] = get_data(cfg)
    
    cfg = get_settings(cfg, data)
    if cfg['group_plot_by'] == lang['group_by_options'][0]: #None
        schoeller = Schoeller(data, cfg)
        plot = schoeller.get_plot()
        st.bokeh_chart(plot)
    else:
        if len(sel_stations) == 0:
            sel_stations = data[st.session_state.station_col].unique()
        for station in sel_stations:
            df = data[data[st.session_state.station_col] == station]
            if len(df)>0:
                cfg['plot_title'] = station
                schoeller = Schoeller(df, cfg)
                plot, df_stats = schoeller.get_plot()
                st.bokeh_chart(plot)
            else:
                st.info(lang['no_record_found_4station'].format(station))
    st.session_state.user.save_config(cn.SCHOELLER_ID, 'default', cfg)

def show_menu():
    set_lang()
    MENU_OPTIONS = lang["menu_options"]
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)

    if menu_action == MENU_OPTIONS[0]:
        show_schoeller_plot()
    elif menu_action == MENU_OPTIONS[1]:
        pass # correlation matrix to come