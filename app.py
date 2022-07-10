#/usr/bin/python3
import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
import requests
from streamlit_option_menu import option_menu  #https://pypi.org/project/streamlit-option-menu/

import helper
import const as cn
from proj.database import get_connection
from menu import menu_home, menu_projects, menu_data, menu_plots, menu_analysis, menu_calculators, menu_login
import os
import session

__version__ = '0.0.3' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-12-28'
APP_NAME = 'Fontus'
APP_EMOJI = '🌎'
GIT_REPO = 'https://github.com/lcalmbach/st-piper'

# -----------------------------------------------------------------------------
# functions
# -----------------------------------------------------------------------------

@st.experimental_memo()
def get_lottie():
    ok=True
    r=''
    try:
        r = requests.get(cn.LOTTIE_URL).json()
    except:
        ok = False
    return r, ok

def show_help_icon():
    help_html = "<a href = '{}' alt='water' target='_blank'><img src='data:image/png;base64,{}' class='img-fluid' style='width:25px;height:25px;'></a><br>".format(
        cn.HELP_SITE, helper.get_base64_encoded_image(cn.HELP_ICON)
    )
    st.sidebar.markdown(help_html, unsafe_allow_html=True)

def main():
    def show_app_name():
        cols = st.sidebar.columns([1,5])
        with cols[0]:
            lottie_search_names, ok = get_lottie()
            if ok:
                st_lottie(lottie_search_names, height=40, loop=True)
        with cols[1]:
            st.markdown(f"### {APP_NAME}\n\n")
    
    def get_app_info():
        return f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
        <small>
        {lang['app_created_by']} <a href="mailto:{__author_email__}">{__author__}</a><br>
        version: {__version__} ({VERSION_DATE})<br>
        {lang['curr_project']}: {st.session_state.project.short_name}<br>
        {lang['logged_in_user']}: {st.session_state.user.full_name}<br>
        language: {st.session_state.language} <br>
        </small>
        """

    st.session_state.conn = get_connection()
    st.set_page_config(page_title=APP_NAME, page_icon=APP_EMOJI, layout="wide", initial_sidebar_state="auto", menu_items=None)
    if 'project' not in st.session_state:
        session.init()
    lang = helper.get_lang(lang=st.session_state.language, py_file=os.path.realpath(__file__) )
    
    MENU_OPTIONS = lang['menu_options']
    
    menu_actions = [menu_home.show_menu
        ,menu_projects.show_menu
        ,menu_data.show_menu
        ,menu_plots.show_menu
        ,menu_analysis.show_menu
        ,menu_calculators.show_menu
        ,menu_login.show_menu
    ]
    if st.session_state.user.is_logged_in():
        MENU_OPTIONS[-1] = lang['logout']
        menu_actions[-1] = menu_login.show_logout_form
    
    show_app_name()
    # see https://icons.getbootstrap.com/ to change the icon
    menu_action = option_menu("", MENU_OPTIONS, 
        icons=['house', 'journal-text', "server", 'graph-up', "search", "calculator", "key"], 
        menu_icon = "cast", default_index=0, orientation="horizontal")
    id = MENU_OPTIONS.index(menu_action)
    menu_actions[id]()
    
    show_help_icon()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)

if __name__ == '__main__':
    main()
