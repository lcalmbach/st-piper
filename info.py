import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

def show_menu(texts_dict: dict):
    text = texts_dict['intro_text']
    st.markdown(text)
    with st.expander("Test Dataset"):
        st.write(st.session_state.current_dataset)
    with st.expander("Columns"):
        df = pd.DataFrame(st.session_state.current_dataset.columns)
        df.columns=['column name']
        AgGrid(df)