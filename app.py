#/usr/bin/python3

import streamlit as st
import pandas as pd
import json
import uuid
from streamlit_lottie import st_lottie
import requests

import const as cn
import info
import sample
import station
import parameter
import data
import plots
from config import Config
import guideline

__version__ = '0.0.1' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-11-03'
APP_NAME = 'Fontus'
APP_EMOJI = '🌎'
GIT_REPO = 'https://github.com/lcalmbach/st-piper'


APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """


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

def main():
    def show_app_name():
        cols = st.sidebar.columns([1,5])
        with cols[0]:
            lottie_search_names, ok = get_lottie()
            if ok:
                st_lottie(lottie_search_names, height=40, loop=True)
        with cols[1]:
            st.markdown(f"### {APP_NAME}\n\n")

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

    if menu_action == 0:
        info.show_menu(texts_dict['info'])
    elif menu_action == 1:
        data.show_menu(texts_dict['data'])
    elif menu_action == 2:
        sample.show_menu(texts_dict['samples'])
    elif menu_action == 3:
        station.show_menu(texts_dict['stations'])
    elif menu_action == 4:
        parameter.show_menu(texts_dict['parameter'])
    elif menu_action == 5:
        plots.show_menu(texts_dict['plots'])
    elif menu_action == 6:
        guideline.show_menu(texts_dict['guideline'])
    else:
        st.write(menu_action)
    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
