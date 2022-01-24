#/usr/bin/python3

import streamlit as st
import pandas as pd
import json
from streamlit_lottie import st_lottie
import requests
import sys

import helper
import const as cn
import home
import projects
import plots
from config import Config

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
    help_html = "<a href = '{}' alt='water' target='_blank'><img src='data:image/png;base64,{}' class='img-fluid' style='width:35px;height:35px;'></a><br>".format(
        cn.HELP_SITE, helper.get_base64_encoded_image("./help1600.png")
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
    
    # LC: moved to menu, should go to menu
    # def show_login_button():
    #     login_request = False
    #     # trial: having a top row for menu options so the sidebar is reserved for the filters and settings.
        
    #     cols = st.columns([9,1])
    #     if st.session_state.config.is_logged_in() == False:
    #         with cols[0]:
    #             st.write('') #workaround, otherwise button appears on the left
    #         with cols[1]:
    #             if st.button('Login'):
    #                 login_request = True
    #     else:
    #         with cols[0]:
    #             st.write('') #workaround, otherwise button appears on the left
    #         with cols[1]:
    #             if st.button('Logout'):
    #                 st.session_state.config.logged_in_user = None
    #     return login_request

    def get_app_info():
        return f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
        <small>
        {lang['app_created_by']} <a href="mailto:{__author_email__}">{__author__}</a><br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        {lang['logged_in_user']}: {st.session_state.config.logged_in_user_name} <br>
        </small>
        """

    st.set_page_config(page_title=APP_NAME, page_icon=APP_EMOJI, layout="wide", initial_sidebar_state="auto", menu_items=None)
    # read file
    
    if len(st.session_state) == 0:
        st.session_state.config = Config()
    
    lang = helper.get_language(sys.argv[0].replace('.py',""), st.session_state.config.language)

    MENU_OPTIONS = lang['menu_options']
    show_app_name()    
    menu_action = st.sidebar.selectbox(lang['menu'], MENU_OPTIONS)
    #login_request = show_login_button()
    #if login_request:
    #    login_result = login.show_form()
    #    print(login_result)
    if menu_action == MENU_OPTIONS[0]:
        home.show_menu()
    elif menu_action == MENU_OPTIONS[1]:
        projects.show_menu()
    elif menu_action == MENU_OPTIONS[2]:
         plots.show_menu()
    # elif menu_action == 7:
    #     guideline.show_menu(texts_dict['guideline'])
    # elif menu_action == 8:
    #     calculator.show_menu(texts_dict['calculator'])
    # else: 
    #     st.write(menu_action)
    
    show_help_icon()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)


if __name__ == '__main__':
    main()
