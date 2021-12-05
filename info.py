import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

def show_menu(texts_dict: dict):
    text = texts_dict['intro_text']
    st.markdown(text)
    if st.session_state.config.data_is_loaded():
        with st.expander("Test Dataset"):
            pass #st.write(st.session_state.current_dataset)
        with st.expander("Columns"):
            pass #df = pd.DataFrame(st.session_state.current_dataset.columns)
            #df.columns=['column name']
            #AgGrid(df)
    else:
        st.markdown(texts_dict['no_data_text'])