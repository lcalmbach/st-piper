import streamlit as st
from helper import flash_text

texts = {}
def verify_password(user, password):
    return True

def show_login_form():
    result = None
    cols = st.columns(2)
    with cols[1]:
        st.write('')
    with cols[0]:
        form = st.form(key='login')
        with form:
            user = st.text_input(label='Username')
            password = st.text_input(label='Password', type='password')
            log_in_button = form.form_submit_button(label='Login')
            if log_in_button:
                if verify_password(user, password):
                    st.session_state.config.logged_in_user = user
                    result = 'ok'
                else:
                    result = 'error'

def show_account_form():
    st.info("Not implemented yet")

def show_create_account_form():
    st.info("Not implemented yet")

def show_logout_form():
    if st.button("Logout"):
        st.session_state.config.logged_in_user = None
        flash_text('You have been successfully logged out', 'success')

def show_menu(texts_dict: dict):
    menu_options = texts_dict["menu_options"]
    menu_options[0] = 'Logout' if st.session_state.config.is_logged_in() else 'Login'
    menu_options[1] = 'Account settings' if st.session_state.config.is_logged_in() else 'Create account'
    menu_action = st.sidebar.selectbox('Options', menu_options)
    
    if st.session_state.config.is_logged_in():
        if menu_action == menu_options[0]:
            show_logout_form()
        elif menu_action == menu_options[1]:
            show_account_form()
    else:
        if menu_action == menu_options[0]:
            show_login_form()
        elif menu_action == menu_options[1]:
            show_create_account_form()

