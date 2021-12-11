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
    MENU_OPTIONS = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Plot type', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        time_series.show_menu(texts_dict['time_series'])
    elif menu_action == MENU_OPTIONS[1]:
        scatter.show_menu(texts_dict['scatter'])
    elif menu_action == MENU_OPTIONS[2]:
        scatter.show_menu(texts_dict['map'])
    elif menu_action == 7:
        piper.show_menu(texts_dict['piper'])
