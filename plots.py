from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np

import piper
import time_series
import map
import scatter

texts_dict = ""


def show_menu(td: dict):
    global texts_dict

    texts_dict = td
    st.session_state.config.geopoint_to_lat_long()
    MENU_OPTIONS = st.session_state.config.get_plots_options()
    menu_action = st.sidebar.selectbox('Plot type', MENU_OPTIONS)
    if menu_action.lower() == 'time series':
        time_series.show_menu(texts_dict['time_series'])
    if menu_action.lower() == 'scatter':
        scatter.show_menu(texts_dict['scatter'])
    if menu_action.lower() == 'map':
        map.show_menu(texts_dict['map'])
    if menu_action.lower() == 'piper':
        piper.show_menu(texts_dict['piper'])
