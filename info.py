import streamlit as st

def show_menu(texts_dict: dict):
    text = texts_dict['intro_text']
    st.markdown(text)
    st.markdown("#### Test Dataset")
    st.write(st.session_state.current_dataset)