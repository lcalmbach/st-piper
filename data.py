from logging import NullHandler
from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np
from value_per_row_import import Value_per_row_import

texts_dict = ""

def check_data_format(df):
    ok = True
    err_msg = ''
    return ok, err_msg


def nwis_test():
    sites = ['331915112400601','332023112372901','320834110580401']
    siteInfo = nwis.get_info(sites=sites)
    st.write(siteInfo[0])
    
    wellDf = nwis.get_record(sites=sites, service='qwdata', start='2000-01-01')
    st.write(wellDf.columns)
    st.write(wellDf.head())
    st.write(wellDf[['p00025','p00003','p00010']])


def load_config():
    pass

def show_menu(td: dict):
    global texts_dict

    texts_dict = td
    MENU_OPTIONS = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        imp = Value_per_row_import(texts_dict['value_per_row_import'])
        imp.run_step()
    elif menu_action == MENU_OPTIONS[1]:
        imp = Value_per_row_import(texts_dict['value_per_row_import'])
        imp.run_step()
    elif menu_action == MENU_OPTIONS[2]:
        load_config()
    else:
        st.write('menu option does not exist')