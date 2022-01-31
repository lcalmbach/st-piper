import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

import const as cn
import helper

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


def show_station_stats():
    st.info(f"{__name__} not implemented yet")

def show_parameters_stats():
    st.info(f"{__name__} not implemented yet")

def show_trend():
    st.info(f"{__name__} not implemented yet")

def show_outliers():
    st.info("not implemented yet")

def show_saturation():
    st.info("not implemented yet")

def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    intro_texts = ['station_stats', 'parameter_stats']
    menu_actions = [show_station_stats
                    ,show_parameters_stats
                    ,show_trend
                    ,show_outliers
                    ,show_saturation]
    id = MENU_OPTIONS.index(menu_action)
    with st.expander('Intro'):
        st.markdown(lang['menu_intro'][id])
    menu_actions[id]
    