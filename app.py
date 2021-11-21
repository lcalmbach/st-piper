from os import sep
from pandas.io.parsers import read_csv
import streamlit as st
from streamlit.elements.arrow import Data
import pandas as pd
import json

import const as cn
import info
import piper
import samples
import data
import helper
from config import Config

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

def main():
    st.set_page_config(page_title=APP_NAME, page_icon=APP_EMOJI, layout="wide", initial_sidebar_state="auto", menu_items=None)
    # read file
    texts_dict = get_texts()
    
    if len(st.session_state) == 0:
        st.session_state.config = Config()

    MENU_OPTIONS = texts_dict["main"]["menu_options"]

    st.sidebar.markdown(f"### {APP_EMOJI} {APP_NAME}")
    menu_action = st.sidebar.selectbox('Menu', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        info.show_menu(texts_dict['info'])
    elif menu_action == MENU_OPTIONS[1]:
        data.show_menu(texts_dict['data'])
    elif menu_action == MENU_OPTIONS[2]:
        samples.show_menu(texts_dict['samples'])
    elif menu_action == MENU_OPTIONS[3]:
        piper.show_menu(texts_dict['piper'])
    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == '__main__':
    main()