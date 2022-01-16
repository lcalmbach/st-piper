import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import const as cn
import sys

from helper import flash_text, get_language, merge_sentences

lang = {}
def set_lang():
    global lang
    lang = get_language(__name__, st.session_state.config.language)

def verify_password(user, password):
    return True


def show_login_form():
    result = None
    cols = st.columns(2)
    with cols[0]:
        form = st.form(key='login')
        with form:
            user = st.text_input(label=lang['username'])
            password = st.text_input(label=lang['password'], type='password')
            log_in_button = form.form_submit_button(label=lang['login'])
            if log_in_button:
                if verify_password(user, password):
                    st.session_state.config.logged_in_user = user
                    result = 'ok'
                else:
                    result = 'error'
    if result == 'ok':
        flash_text(lang["login_confirmation"], 'success')


def show_account_form():
    st.info("Not implemented yet")

def show_create_account_form():
    st.info("Not implemented yet")


def show_logout_form():
    if st.button(lang['logout']):
        st.session_state.config.logged_in_user = None
        flash_text(lang["logout_confirmation"], 'success')


def show_info():
    def set_language():
        languages = cn.LANGAUAGE_DICT
        id = list(languages.keys()).index(st.session_state.config.language)
        old_id = st.session_state.config.language
        st.session_state.config.language = st.selectbox(lang['select_language'], list(languages.keys()),
                    format_func=lambda x: languages[x], index=id)
        # rerender entire script if language has changed
        if st.session_state.config.language != old_id:
            st.experimental_rerun()

    st.image(f"./{cn.SPLASH_IMAGE}")
    st.markdown(f"### {lang['intro_title']}")
    text = merge_sentences((lang['intro_body']))
    st.markdown(text, unsafe_allow_html=True)

    if not(st.session_state.config.is_logged_in()):
        set_language()
    
    projects = st.session_state.config.project_dict
    
    st.session_state.config.current_project = st.selectbox(lang["select_project"], projects.keys(),
                format_func=lambda x: projects[x])
    st.markdown(f"**{st.session_state.config.current_project['name']}**")
    st.markdown(st.session_state.config.current_project['description'])

def show_menu():
    set_lang()
    menu_options = lang['menu_options']
    # set the menuoption for login/logout to the corresponding expression depending on the current state
    menu_options[1] = lang['logout'] if st.session_state.config.is_logged_in() else lang['login']
    menu_options[2] = lang['account_settings'] if st.session_state.config.is_logged_in() else lang['create_account']
    menu_action = st.sidebar.selectbox(lang['options'], menu_options) 
    if menu_action == menu_options[0]:
        show_info()
    elif menu_action == menu_options[1]:
        if st.session_state.config.is_logged_in():
            show_logout_form()
        else :
            show_login_form()
    elif menu_action == menu_options[2]:
        if st.session_state.config.is_logged_in():
            show_account_form()
        else :
            show_create_account_form()