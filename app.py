#/usr/bin/python3
import streamlit as st
import pandas as pd
import json
from streamlit_lottie import st_lottie
import requests
import sys
from streamlit_option_menu import option_menu

from fontus.project import Project
from fontus.user import User
import helper
import const as cn
import home
import menu_projects
import menu_plots
from database import get_connection
import login
import menu_calculator
import menu_analysis
import menu_data
from query import qry
import database as db

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
        {lang['curr_project']}: {st.session_state.project.short_name} <br>
        {lang['logged_in_user']}: {st.session_state.user.email} <br>
        language: {st.session_state.language} <br>
        </small>
        """

    st.session_state.conn = get_connection()
    st.set_page_config(page_title=APP_NAME, page_icon=APP_EMOJI, layout="wide", initial_sidebar_state="auto", menu_items=None)
    # read file
    if 'project' not in st.session_state:
        st.session_state.user = User(cn.DEFAULT_USER_ID)
        st.session_state.project = Project(cn.DEFAULT_PROJECT_ID)
        st.session_state.language = st.session_state.user.language
        st.session_state.project_dict = st.session_state.user.get_project_dict()
    lang = helper.get_language(sys.argv[0].replace('.py',""), st.session_state.language)
    
    MENU_OPTIONS = lang['menu_options']
    
    menu_actions = [home.show_menu
        ,menu_projects.show_menu
        ,menu_data.show_menu
        ,menu_plots.show_menu
        ,menu_analysis.show_menu
        ,menu_calculator.show_menu
        ,login.show_menu
    ]
    if st.session_state.user.is_logged_in():
        MENU_OPTIONS[-1] = lang['logout']
        menu_actions[-1] = login.show_logout_form
    
    show_app_name()
    menu_action = option_menu(None, MENU_OPTIONS, 
        icons=['house', 'journal-text', "table", 'bar-chart-fill', "search", "calculator", "key"], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    id = MENU_OPTIONS.index(menu_action)
    menu_actions[id]()
    
    show_help_icon()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)

if __name__ == '__main__':
    main()
