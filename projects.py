import streamlit as st
import pandas as pd
import dataretrieval.nwis as nwis
from st_aggrid import AgGrid
import numpy as np

from value_per_row_import import Value_per_row_import
from sample_per_row_import import Sample_per_row_import
import sample
import station
import parameter_menu
import const as cn
from helper import get_language, flash_text


lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.config.language)


def check_data_format(df):
    ok = True
    err_msg = ''
    return ok, err_msg


def nwis_test():
    """
    todo!
    """
    sites = ['331915112400601','332023112372901','320834110580401']
    siteInfo = nwis.get_info(sites=sites)
    st.write(siteInfo[0])
    
    wellDf = nwis.get_record(sites=sites, service='qwdata', start='2000-01-01')
    st.write(wellDf.columns)
    st.write(wellDf.head())
    st.write(wellDf[['p00025','p00003','p00010']])


def create_project():
    if not (st.session_state.config.is_logged_in()):
        st.info(lang['must_be_logged_in'])
    else:
        result = ''
        form = st.form(key='proj')
        with form:
            name = st.text_input(label=lang['project_name'])
            description = st.text_area(label=lang['Description'])
            cols = st.columns(2)
            with cols[0]:
                date_format = st.selectbox(lang['date_field_format'], options=cn.DATE_FORMAT_LIST)
                format_options = [lang['value_per_row'], lang['sample_per_row']]
                file_format = st.selectbox(label=lang['data_format'], options=format_options)
            with cols[1]:
                encoding = st.selectbox(label=lang['data_format'], options=cn.ENCODINGS)
                is_public = st.checkbox(label=lang['dataset_is_public'], help=lang['dataset_is_public_help'])
            
            cols = st.columns((1,1,6))
            with cols[0]:
                save_button = form.form_submit_button(label=lang['save'])
            with cols[1]:
                cancel_button = form.form_submit_button(label=lang['cancel'])
            if save_button:
                result = 'ok'
            if cancel_button:
                result = 'cancel'

        if result == 'ok' :
            flash_text(lang['project_created_confirmation'], 'success')


def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox(label=lang['options'], options=MENU_OPTIONS)
    if menu_action == MENU_OPTIONS[0]:
        create_project()
    elif menu_action == MENU_OPTIONS[1]:
        imp = Value_per_row_import()
        imp.run_step()
    elif menu_action == MENU_OPTIONS[2]:
        imp = Sample_per_row_import()
        imp.run_step()
    elif menu_action == MENU_OPTIONS[3]:
        sample.show_menu()
    elif menu_action == MENU_OPTIONS[4]:
        station.show_menu()
    elif menu_action == MENU_OPTIONS[5]:
        parameter_menu.show_menu()