from numpy import NAN
import streamlit as st
import pandas as pd
import const as cn
from st_aggrid import AgGrid
import numpy as np
from helper import transpose_row

texts_dict = ""

def show_summary():
    fields = st.session_state.sample_station_cols
    df_samples = st.session_state.row_sample_df[fields]
    df_samples = df_samples.sort_values(st.session_state.station_col)
    st.markdown(f"Number of samples: {len(df_samples)}")
    AgGrid(df_samples)


def show_detail():
    df = st.session_state.row_value_df
    x = st.session_state.key2col()
    station_key = x[cn.STATION_IDENTIFIER_COL]
    date_col = x[cn.SAMPLE_DATE_COL]
    # st.write(list(df[date_col]))
    lst_stations = list(df[station_key].astype(str).unique())
    station = st.sidebar.selectbox("Station", options=lst_stations)
    lst_samples = list(df[df[station_key] == station][date_col].unique())
    lst_samples.sort()
    sampling_date = st.sidebar.selectbox("Sample", options=lst_samples)
    df = st.session_state.row_value_df
    df = df[(df[station_key] == station) & (df[date_col]==sampling_date)]
    if st.session_state.col_is_mapped(cn.CATEGORY_COL):
        lst_categories = st.session_state.parameter_categories()

        sel_categories = st.sidebar.multiselect('🔎 Parameter categories', lst_categories)
        if len(sel_categories) > 0:
            category_col = x[cn.CATEGORY_COL]
            df_filtered = df[df[category_col].isin(sel_categories)]
            if len(df_filtered) > 0:
                df = df_filtered
            else:
                st.info("No values found using this filter, reverting to no filter")
    
    df_station_info = df[st.session_state.station_cols].drop_duplicates()
    df_sample_info = df[st.session_state.sample_cols].drop_duplicates()
    df_analysis_info = df[st.session_state.get_parameter_detail_form_columns()]
    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Sample")
        AgGrid(transpose_row(df_sample_info))
    with cols[1]:
        st.markdown("#### Station")
        AgGrid(transpose_row(df_station_info))
    st.markdown("#### Observations")
    AgGrid(df_analysis_info)

def show_menu(td: dict):
    global texts_dict
    texts_dict = td
    menu_options = td['menu_options']
    sel_option = st.sidebar.selectbox("Options", menu_options)
    if sel_option == td['menu_options'][0]:
        st.markdown("### Samples summary")
        show_summary()
    elif sel_option == td['menu_options'][1]:
        show_detail()
