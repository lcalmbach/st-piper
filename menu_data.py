from argparse import _StoreFalseAction
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd

import const as cn
import helper
from query import qry
import database as db

project = {}
lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)



def show_stations():
    st.markdown(F"#### Stations")
    sql = qry['station_data'].format(st.session_state.config.project.key)
    df = project.station_data()
    settings = {'height':400, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
    cols=[]
    grid_response = helper.show_table(df,cols, settings)
    
    if len(grid_response)>0:
        st.markdown(F"#### Samples")
        station_id = grid_response.iloc[0]['id']
        sql = qry['station_samples'].format(st.session_state.config.project.key, station_id)
        df = project.station_samples(station_id)
        grid_response = helper.show_table(df,cols, settings)

    if len(grid_response)>0:
        st.markdown(F"#### Observations")
        sample_date = grid_response.iloc[0]['sampling_date']
        df = project.sample_observations(station_id, sample_date)
        cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
        grid_response = helper.show_table(df,cols, settings)

def show_parameters():
    obs_filter = helper.get_filter(['stations', 'sampling_date'])
    st.markdown(F"#### Parameters")
    df = project.parameter_data()
    cols = []
    cols.append({'name': 'id', 'type': 'int', 'precision': 0, 'hide':True})
    settings = {'height':400, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
    grid_response = helper.show_table(df,cols, settings)
    if len(grid_response)>0:
        st.markdown(F"#### Observations")
        parameter_id = grid_response.iloc[0]['id']
        df = project.parameter_observations(parameter_id, obs_filter)
        cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'is_non_detect', 'type': 'int', 'precision': 0, 'hide':True})
        grid_response = helper.show_table(df,cols, settings)
    
    if len(grid_response)>0:
        st.markdown(F"#### Sample")
        station_id = grid_response.iloc[0]['station_id']
        sample_date = grid_response.iloc[0]['sampling_date']
        df = project.sample_observations(station_id, sample_date)
        cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
        grid_response = helper.show_table(df,cols, settings)



def show_trend():
    st.info("not implemented yet")

def show_outliers():
    st.info("not implemented yet")

def show_saturation():
    st.info("not implemented yet")

def show_menu():
    global project 
    set_lang()

    project = st.session_state.config.project
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    MENU_FUNCTIONS = [show_stations, show_parameters, show_trend, show_outliers, show_saturation]
    id = MENU_OPTIONS.index(menu_action)
    MENU_FUNCTIONS[id]()
