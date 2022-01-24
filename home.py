import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import const as cn
import sys
import database as db
from query import qry 
from passlib.context import CryptContext
import random

import helper

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


def get_crypt_context():
    return CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=50000
    )


def is_valid_password(usr: str, pwd: str)->bool:
    """
    Passwörter werden gehasht in der DB abgelegt
    """
    
    context = get_crypt_context()
    
    sql = qry['get_usr_pwd'].format(usr)    
    hashed_db_password, ok, err_msg = db.get_value(sql, st.session_state.config.conn)
    if ok:
        ok = context.verify(pwd, hashed_db_password)
    else:
        ok = False
    return ok

def reset_password(usr):
    """
    generates a random number, and stores it hashed for the user record. then fontus sends the number ot the users email.
    """

    ok = True
    err_msg = ''
    sql = qry['user_info'].format(usr)
    st.write(sql)
    df, ok, err_msg = db.execute_query(sql, st.session_state.config.conn)
    if ok and len(df) > 0:
        pwd_new = '{:07d}'.format(random.randint(0, 999999))
        context = get_crypt_context()
        sql = qry['change_pwd'].format(context.hash(pwd_new), usr)
        ok, err_msg = db.execute_non_query(sql, st.session_state.config.conn)
        if ok:
            #save to database
            ok, message = db.execute_non_query(sql, st.session_state.config.conn)
            if ok:
                subject = 'Fontus Password reset'
                emails = [df.iloc[0]['email']]
                content = f"""<html>
                    <head></head>
                    <body>
                        <p>Hi {df.iloc[0]['first_name']}<br>
                        your password was reset to <b>{pwd_new}</b>. Please change it after your first login in the 
                        account settings.<br><br>Have a great day<br>
                        fontus-bot@your.service
                    </body>
                    </html>
                """
                mail = helper.Mail()
                mail.send(emails, subject, content)
                message = f"Password was successfully reset and sent to {df.iloc[0]['email']}"
        else:
            message = "Password could not be reset"
    else:
        message = f"User {usr} could not be found. Please verify spelling or create a new account."
    return ok, message

def show_login_form():
    ok = True
    message = ''
    st.markdown('## 👤Login')
    with st.form('login_form'):
        action = ''
        usr = st.text_input('username')
        pwd = st.text_input('password', type='password')
        col1, col2 = st.columns((1,12))
        st.session_state.logged_in = False
        with col1:
            if st.form_submit_button(label='Login'):     
                action = 'login'           
                if is_valid_password(usr, pwd):
                    st.session_state.config.logged_in_user = usr
                    st.session_state.logged_in = True
                    sql = qry['user_info'].format(usr)
                    df, ok, message = db.execute_query(sql, st.session_state.config.conn)
                    if ok:
                        st.session_state.config.logged_in_user = df.iloc[0]['email']
                        message = f"Welcome back {df.iloc[0]['first_name']}"
                else:
                    ok=False
                    message = 'Login was unsuccessful. Verify user and password or reset your password'
        with col2:
            if st.form_submit_button(label='Reset Password'):
                action = 'reset'
                ok, message = reset_password(usr)

    #if key was pressed
    if action in ('login','reset'):
        if ok:
            helper.flash_text(message, 'success')
        else:
            helper.flash_text(message, 'warning')
    


def show_account_form():
    st.info("Not implemented yet")


def show_create_account_form():
    st.info("Not implemented yet")


def show_logout_form():
    if st.button(lang['logout']):
        st.session_state.config.logged_in_user = None
        helper.flash_text(lang["logout_confirmation"], 'success')


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
    text = helper.merge_sentences((lang['intro_body']))
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