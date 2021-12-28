#/usr/bin/python3

import streamlit as st
import pandas as pd
import json
import uuid
from streamlit_lottie import st_lottie
import requests

import helper
import const as cn
import info
import sample
import station
import parameter
import data
import plots
from config import Config
import guideline
import calculator
import login

__version__ = '0.0.3' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-12-28'
APP_NAME = 'Fontus'
APP_EMOJI = '🌎'
GIT_REPO = 'https://github.com/lcalmbach/st-piper'


def get_data():
    df = pd.read_csv(cn.TEST_DATASET, sep=';')
    df = data.calc_meql(df)
    df = data.calc_pct(df)
    return df

def get_texts():
    with open('texts.json', 'r') as myfile:
        data=myfile.read()
    return json.loads(data)

@st.experimental_memo()
def get_lottie():
    ok=True
    r=''
    try:
        r = requests.get(cn.LOTTIE_URL).json()
    except:
        st.write(r.status)
        ok = False
    return r,ok

def show_help_icon():
    help_html = "<a href = '{}' alt='Girl in a jacket' target='_blank'><img src='data:image/png;base64,{}' class='img-fluid' style='width:45px;height:45px;'></a><br>".format(
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
    
    def show_login_button():
        login_request = False
        # trial: having a top row for menu options so the sidebar is reserved for the filters and settings.
        
        cols = st.columns([9,1])
        if st.session_state.config.is_logged_in() == False:
            with cols[0]:
                st.write('') #workaround, otherwise button appears on the left
            with cols[1]:
                if st.button('Login'):
                    login_request = True
        else:
            with cols[0]:
                st.write('') #workaround, otherwise button appears on the left
            with cols[1]:
                if st.button('Logout'):
                    st.session_state.config.logged_in_user = None
        return login_request

    def get_app_info():
        return f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
        <small>
        App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        logged in user: {st.session_state.config.logged_in_user_name} <br>
        </small>
        """

    st.set_page_config(page_title=APP_NAME, page_icon=APP_EMOJI, layout="wide", initial_sidebar_state="auto", menu_items=None)
    # read file
    texts_dict = get_texts()
    
    if len(st.session_state) == 0:
        st.session_state.config = Config()
        st.session_state.key = uuid.uuid4()

    MENU_OPTIONS = st.session_state.config.get_menu_options()
    show_app_name()    
    menu_action = st.sidebar.selectbox('Menu', list(MENU_OPTIONS.keys()),
        format_func=lambda x: MENU_OPTIONS[x])
    
    #login_request = show_login_button()
    #if login_request:
    #    login_result = login.show_form()
    #    print(login_result)
        
    if menu_action == 0:
        info.show_menu(texts_dict['info'])
    elif menu_action == 1:
        data.show_menu(texts_dict['data'])
    elif menu_action == 2:
        login.show_menu(texts_dict['login'])
    elif menu_action == 3:
        sample.show_menu(texts_dict['samples'])
    elif menu_action == 4:
        station.show_menu(texts_dict['stations'])
    elif menu_action == 5:
        parameter.show_menu(texts_dict['parameter'])
    elif menu_action == 6:
        plots.show_menu(texts_dict['plots'])
    elif menu_action == 7:
        guideline.show_menu(texts_dict['guideline'])
    elif menu_action == 8:
        calculator.show_menu(texts_dict['calculator'])
    else:
        st.write(menu_action)
    show_help_icon()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)


if __name__ == '__main__':
    main()
