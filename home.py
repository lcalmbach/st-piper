import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import const as cn
import sys
import database as db
from query import qry 
from passlib.context import CryptContext
import random
from fontus import User, Project

import const
import helper
import login

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

def encrypt_password(self, password):
    return CryptContext.encrypt(password)

def is_valid_password(usr: str, pwd: str)->bool:
    """
    Passwörter werden gehasht in der DB abgelegt
    """
    
    context = get_crypt_context()
    
    sql = qry['get_usr_pwd'].format(usr)    
    hashed_db_password, ok, err_msg = db.get_value(sql, st.session_state.conn)
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
    df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
    if ok and len(df) > 0:
        pwd_new = '{:07d}'.format(random.randint(0, 999999))
        context = get_crypt_context()
        sql = qry['change_pwd'].format(context.hash(pwd_new), usr)
        ok, err_msg = db.execute_non_query(sql, st.session_state.conn)
        if ok:
            #save to database
            ok, message = db.execute_non_query(sql, st.session_state.conn)
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
        email = st.text_input('username')
        pwd = st.text_input('password', type='password')
        col1, col2 = st.columns((1,12))
        st.session_state.logged_in = False
        with col1:
            if st.form_submit_button(label='Login'):     
                action = 'login'           
                if is_valid_password(email, pwd):
                    st.session_state.config.logged_in_user = email
                    st.session_state.logged_in = True
                    user = User(email)
                    if user != None:
                        st.session_state.config.logged_in_user = user.email
                        st.session_state.config.language = user.language
                        st.session_state.config.user = user
                        message = f"Welcome back {user.first_name}"
                else:
                    ok=False
                    message = 'Login was unsuccessful. Verify user and password or reset your password'
        with col2:
            if st.form_submit_button(label='Reset Password'):
                action = 'reset'
                ok, message = reset_password(email)

    #if key was pressed
    if action in ('login','reset'):
        if ok:
            helper.flash_text(message, 'success')
            st.experimental_rerun()
        else:
            helper.flash_text(message, 'warning')
        
    
def show_account_form():
    def compare_passwords(pwd1, pwd2):
        ok = (pwd1 > '' and pwd1 == pwd2)
        if not ok:
            message = "Passwords do not match, please try again"
        else:
            message = ""
        return ok, message

    message = ''
    ok = False
    st.markdown("#### Account Settings")
    with st.form('login_form'):
        email = st.session_state.config.logged_in_user
        user = User(email)
        user.first_name = st.text_input('First name', user.first_name)
        user.last_name = st.text_input('Last name', user.last_name)
        user.company = st.text_input('Company', user.company)
        country_dict = helper.get_country_list()
        id = list(country_dict.keys()).index(user.country)
        user.country = st.selectbox('Country', 
            options = list(country_dict.keys()),
            format_func=lambda x: country_dict[x],
            index = id)
        id = list(const.LANGAUAGE_DICT.keys()).index(user.language)
        user.language = st.selectbox('Language', 
            options = list(const.LANGAUAGE_DICT.keys()),
            format_func=lambda x: const.LANGAUAGE_DICT[x],
            index = id)

        if st.form_submit_button(label='Save'):     
            ok, message = user.save()

    st.markdown("#### Change Password")
    with st.form('Change password'):
        pwd1 = st.text_input('New Password', type='password')
        pwd2 = st.text_input('Confirm Password', type='password')
        if st.form_submit_button(label='Save Password'):
            ok, message = compare_passwords(pwd1, pwd2) 
            if ok:
                context = get_crypt_context()
                ok, message = user.save_password(context.hash(pwd1))
            message_type = 'success' if ok else 'warning'
    
    st.markdown("#### Delete Account")
    with st.form('delete_account'):
        st.markdown("Account and all associated datasets will be deleted. Enter your email-address to confirm this operation.")
        email = st.text_input("Acccount Email")
        
        if st.form_submit_button(label='Delete account'):
            if email == st.session_state.config.user.email:
                ok, message = st.session_state.config.user.delete()
                    
                message_type = 'success' if ok else 'warning'
            else:
                message, message_type = "Enter your correct email address", True

    #if key was pressed
    message_type = 'success' if ok else 'warning'
    if message > '':
        helper.flash_text(message, message_type)

def show_create_account_form():
    st.info("Not implemented yet")


def show_info():
    def set_language():
        languages = cn.LANGAUAGE_DICT
        id = list(languages.keys()).index(st.session_state.config.language)
        old_id = st.session_state.config.language
        st.session_state.config.language = st.sidebar.selectbox(lang['select_language'], list(languages.keys()),
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
    prj_id = st.selectbox(lang["select_project"], projects.keys(),
                format_func=lambda x: projects[x])
    prj = Project(prj_id)
    st.session_state.config.project = prj
    st.markdown(f"**{prj.title}**")
    st.markdown(prj.description)

def show_menu():
    set_lang()

    MENU_OPTIONS = lang['menu_options']
    
    menu_actions = [show_info,
                    show_account_form]
    if not st.session_state.config.is_logged_in():
        menu_actions[-1] = login.show_create_account_form
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    id = MENU_OPTIONS.index(menu_action)
    menu_actions[id]()
    