from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np

import piper_menu
import time_series_menu
import map_menu
import histogram_menu
import boxplot_menu
import scatter_menu

texts_dict = ""


def show_menu(td: dict):
    global texts_dict
    texts_dict = td
    #if st.session_state.config.col_is_mapped(cn.GEOPOINT_COL):
    #    st.session_state.config.geopoint_to_lat_long()
    MENU_OPTIONS = st.session_state.config.get_plots_options()
    menu_action = st.sidebar.selectbox('Plot type', MENU_OPTIONS)

    if menu_action.lower() == 'time series':
        time_series_menu.show_menu(texts_dict['time_series'])
    elif menu_action.lower() == 'scatter':
        scatter_menu.show_menu(texts_dict['scatter'])
    elif menu_action.lower() == 'map':
        map_menu.show_menu(texts_dict['map'])
    elif menu_action.lower() == 'piper':
        piper_menu.show_menu(texts_dict['piper'])
    elif menu_action.lower() == 'histogram':
        histogram_menu.show_menu(texts_dict['histogram'])
    elif menu_action.lower() == 'boxplot':
        histogram_menu.show_menu(texts_dict['boxplot'])
    else:
        st.info(f'Plot {menu_action} has is not implemented yet')
