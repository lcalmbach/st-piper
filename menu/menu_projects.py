import streamlit as st
import pandas as pd
import dataretrieval.nwis as nwis
from st_aggrid import GridUpdateMode

#import menu_parameter
import const as cn
import helper
from proj.project import Project
from query import qry
import database as db


lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


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
    st.markdown(siteInfo[0])
    
    wellDf = nwis.get_record(sites=sites, service='qwdata', start='2000-01-01')
    st.write(wellDf.columns)
    st.write(wellDf.head())
    st.write(wellDf[['p00025','p00003','p00010']])


def show_project_form(project:Project, can_edit: bool):
    """Displays form for editing the project metadata: name, description, parameters required for the import

    Args:
        project (Project): project instance
        can_edit (bool): flag to determine if save button is shown
    """
    ok, message = True, ''
    form = st.form(key='proj')
    with form:
        st.markdown("**Project description**")
        project.title = st.text_input(label=lang['project_name'], value=project.title)
        project.description = st.text_area(label=lang['description'], value=project.description)
        project.is_public = st.checkbox(label=lang['dataset_is_public'], value = project.is_public, help=lang['dataset_is_public_help'])
        st.markdown("**Source import file parameters**")
        cols = st.columns(2)
        with cols[0]:
            id = cn.DATE_FORMAT_LIST.index(project.date_format)
            project.date_format = st.selectbox(lang['date_field_format'], options=cn.DATE_FORMAT_LIST, index=id)
            
            seperator_options = [';', ',', '|', 'tab']
            id = seperator_options.index(project.separator)
            project.separator = st.selectbox(label=lang['separator_char'], options=seperator_options, index=id)
            project.has_separate_station_file = st.checkbox('Has separate data source file for station data', value=project.has_separate_station_file)
        with cols[1]:
            id = cn.ENCODINGS.index(project.encoding)
            project.encoding = st.selectbox(label=lang['file_encoding'], options=cn.ENCODINGS, index=id)
            
            format_options = helper.get_lookup_code_dict(category=cn.ENUMS.import_row_format, lang=st.session_state.language)
            id = list(format_options.keys()).index(project.row_is)
            project.row_is = st.selectbox(label=lang['data_format'], options=list(format_options.keys()), 
                format_func=lambda x:format_options[x],
                index=id)

        if form.form_submit_button(label=lang['save']):
            if can_edit:
                ok, message = project.save()
                st.session_state.projects_df = st.session_state.user.get_projects()
            else:
                helper.flash_text(lang['save_warning'], 'warning')
    
    if message > '':
        type = 'success' if ok else 'warning'
        helper.flash_text(message, type) 

def import_data():
    st.session_state.project.import_data()
    
def define_import():
    st.session_state.project.imp.select_step()

def export_data():
    st.write('todo!')

def create_project():
    project = Project(-1)
    show_project_form(project, can_edit=True)

def select_project_from_grid():
    df = st.session_state.project_df[['id', 'title']]
    settings = {}
    settings['height'] = 200
    settings['width'] = "400px"
    settings['selection_mode']='single'
    settings['fit_columns_on_grid_load'] = True
    settings['update_mode'] = GridUpdateMode.SELECTION_CHANGED
    cols = []
    cols.append({'name': 'id', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0, 'hide':True})
    sel_row = helper.show_table(df,cols,settings)
    if len(sel_row)>0:
        return int(sel_row.iloc[0]['id'])
    else:
        return -1

def edit_project():
    st.markdown(f"#### {lang['projects']}")

    project_id = select_project_from_grid()
    if project_id > 0:
        project = Project(project_id)
        show_project_form(project= project, can_edit=project.get_user_permission(st.session_state.user.id)==cn.PERMISSION.Write.value)


def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    if not st.session_state.user.is_logged_in() and 1==2:
        st.info(lang['must_be_logged_in'])
    else:
        menu_actions = [edit_project
                        , create_project
                        , define_import
                        , import_data
                        , export_data]
        id = MENU_OPTIONS.index(menu_action)
        menu_actions[id]()