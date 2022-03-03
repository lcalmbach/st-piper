from logging import NullHandler
import streamlit as st
import const as cn

import piper_menu
import time_series_menu
import map_menu
import menu_histogram
import menu_boxplot
import scatter_menu
import schoeller_menu
import menu_boxplot
from helper import get_language, flash_text

lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.config.language)

def show_menu():
    set_lang()

    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox(lang['plot_type'], MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        time_series_menu.show_menu()
    elif menu_action == MENU_OPTIONS[1]:
        scatter_menu.show_menu()
    elif menu_action == MENU_OPTIONS[2]:
        map_menu.show_menu()
    elif menu_action == MENU_OPTIONS[3]:
        piper_menu.show_menu()
    elif menu_action == MENU_OPTIONS[4]:
        menu_histogram.show_menu()
    elif menu_action == MENU_OPTIONS[5]:
        schoeller_menu.show_menu()
    elif menu_action == MENU_OPTIONS[6]:
        menu_boxplot.show_menu()
    else:
        # temp
        st.info(f'Plot {menu_action} has is not implemented yet').format
