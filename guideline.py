from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np

from value_per_row_import import Value_per_row_import
from sample_per_row_import import Sample_per_row_import
import const as cn

texts_dict = ""

def show_guidelines():
    gl = {}
    with st.expander("Info"):
        st.markdown(texts_dict['info'])
    for index,row in st.session_state.config.guidelines_df.iterrows():
       gl[row['key']] = st.checkbox(row['name'], True)
    selected = { key:value for (key,value) in gl.items() if value == True}

    df = st.session_state.config.guidelines_data_df
    df = df[df['key'].isin(selected.keys())]
    par_options = [None] + list(st.session_state.config.parameter_map_df.index)
    sel_parameter = st.selectbox("Select a parameter", par_options)
    if sel_parameter != None:
        casnr = st.session_state.config.par2casnr()[sel_parameter]
        df = df[df['casnr'] == casnr ]
    if len(df) > 0:
        AgGrid(df)
    else:
        st.info(f"No guideline values for *{sel_parameter}* could be found in the selected guidelines")


def show_menu(td: dict):
    global texts_dict

    texts_dict = td
    MENU_OPTIONS = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        st.markdown("### Guidelines")
        show_guidelines()
    
    else:
        st.write('menu option does not exist')