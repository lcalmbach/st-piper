import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

def show_menu(texts_dict: dict):
    text = texts_dict['intro_text']
    st.markdown(text)
    if st.session_state.config.data_is_loaded():
        st.markdown(f"---")
        st.markdown(f"#### Current dataset:")
        st.markdown(f"**{st.session_state.config.current_dataset['name']}**")
        st.markdown(st.session_state.config.current_dataset['description'])
        img = st.session_state.config.current_dataset['image']
        if img != '':
            st.image(img)
        with st.expander("Columns"):
            df = pd.DataFrame(st.session_state.config.column_map_df.index)
            AgGrid(df)
        
    else:
        st.markdown(texts_dict['no_data_text'])