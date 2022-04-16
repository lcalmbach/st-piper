from logging import NullHandler
import streamlit as st
import const as cn

import menu_piper
import menu_time_series
import menu_map
import menu_histogram
import menu_boxplot
import menu_scatter
import menu_schoeller
import menu_boxplot
from helper import get_language, flash_text

lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.language)

def show_menu():
    set_lang()

    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox(lang['plot_type'], MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        menu_time_series.show_menu()
    elif menu_action == MENU_OPTIONS[1]:
        menu_scatter.show_menu()
    elif menu_action == MENU_OPTIONS[2]:
        menu_map.show_menu()
    elif menu_action == MENU_OPTIONS[3]:
        menu_piper.show_menu()
    elif menu_action == MENU_OPTIONS[4]:
        menu_histogram.show_menu()
    elif menu_action == MENU_OPTIONS[5]:
        menu_schoeller.show_menu()
    elif menu_action == MENU_OPTIONS[6]:
        menu_boxplot.show_menu()
    else:
        # temp
        st.info(f'Plot {menu_action} has is not implemented yet').format
