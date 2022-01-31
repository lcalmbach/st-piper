import streamlit as st
import pandas as pd
import dataretrieval.nwis as nwis
from st_aggrid import GridUpdateMode
import numpy as np

from value_per_row_import import Value_per_row_import
from sample_per_row_import import Sample_per_row_import
import sample
import station
import menu_parameter
import const as cn
import helper
from fontus import Project
from query import qry
import database as db


lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


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


def show_project_form(project:Project):
    if not (st.session_state.config.is_logged_in()):
        st.info(lang['must_be_logged_in'])
    else:
        ok, message = True, ''
        form = st.form(key='proj')
        with form:
            project.title = st.text_input(label=lang['project_name'], value=project.title)
            project.description = st.text_area(label=lang['description'], value=project.description)
            cols = st.columns(2)
            with cols[0]:
                id = cn.DATE_FORMAT_LIST.index(project.date_format)
                project.date_format = st.selectbox(lang['date_field_format'], options=cn.DATE_FORMAT_LIST, index=id)
                format_options = [lang['value_per_row'], lang['sample_per_row']]
                id = format_options.index(project.row_is)
                project.row_is = st.selectbox(label=lang['data_format'], options=format_options, index=id)
            with cols[1]:
                id = cn.ENCODINGS.index(project.encoding)
                project.encoding = st.selectbox(label=lang['data_format'], options=cn.ENCODINGS, index=id)
                project.is_public = st.checkbox(label=lang['dataset_is_public'], value = project.is_public, help=lang['dataset_is_public_help'])
            
            if form.form_submit_button(label=lang['save']):
                ok, message = project.save()
                st.session_state.config.projects_df = st.session_state.config.get_projects()
        
        if message > '':
            type = 'success' if ok else 'warning'
            helper.flash_text(message, type) 

def find_project():
    st.write('todo!')

def import_data():
    st.write('todo!')

def export_data():
    st.write('todo!')

def create_project():
    project = Project(-1)
    show_project_form(project)


def edit_project():
    df = st.session_state.config.projects_df[['id', 'title']]
    settings = {}
    settings['height'] = 100
    settings['width'] = "400px"
    settings['selection_mode']='single'
    settings['fit_columns_on_grid_load'] = True
    settings['update_mode']=GridUpdateMode.SELECTION_CHANGED
    cols = []
    cols.append({'name': 'id', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0, 'hide':True})
    sel_row = helper.show_table(df,cols,settings)
    if len(sel_row) > 0:
        project = Project(sel_row.iloc[0]['id'])
        show_project_form(project)


def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if not st.session_state.config.is_logged_in():
        st.info("You need to be logged in to create, upload and manage projects.")
    else:
        menu_actions = [edit_project
                        , create_project
                        , import_data
                        , export_data]
        id = MENU_OPTIONS.index(menu_action)
        with st.expander('Intro'):
            st.markdown(lang['menu_intro'][id])
        menu_actions[id]()