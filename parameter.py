import streamlit as st
import pandas as pd
import const as cn
from st_aggrid import AgGrid
# import numpy as np
import helper

texts_dict = ""

def show_summary():
    def calc_stats():
        df = st.session_state.config.row_value_df
        par_col = st.session_state.config.key2col()[cn.PARAMETER_COL]
        val_col = st.session_state.config.key2col()[cn.VALUE_NUM_COL]
        if st.session_state.config.col_is_mapped(cn.CATEGORY_COL):
            category_col = st.session_state.config.key2col()[cn.CATEGORY_COL]
            par_group = [category_col, par_col]
        else:
            par_group = [par_col]
        if st.session_state.config.col_is_mapped(cn.UNIT_COL):
            par_group.append(st.session_state.config.key2col()[cn.UNIT_COL])
        stats = df.groupby(par_group)[val_col].agg(['min','max','mean', 'std', 'count']).reset_index()
        stats = stats.sort_values(par_group)
        return stats

    def get_count_stats(df):
        df['const'] = 'x'
        _stats = df.groupby(['const'])['count'].agg(['min','max','mean', 'std', 'count', helper.percentile(10), helper.percentile(90)]).reset_index()
        _stats = _stats.iloc[0].to_dict()
        df.drop('const', axis=1, inplace=True)
        return _stats

    def filter_stats(df):
        st.sidebar.markdown('🔎 Filter')
        if st.session_state.config.col_is_mapped(cn.CATEGORY_COL):
            par_cat_col = st.session_state.config.key2col()[cn.CATEGORY_COL]
            lst_parameter_categories = ['Select a category']
            lst_parameter_categories.extend(list(df[par_cat_col].unique()))
            sel_parameter_category = st.sidebar.selectbox('Parameter category', lst_parameter_categories)
            if sel_parameter_category != lst_parameter_categories[0]:
                df = df[df[par_cat_col] == sel_parameter_category]
        return df

    def show_result(df):
        stats_dict = get_count_stats(df)
        st.markdown(f"Number of parameters: {len(df)}")
        st.markdown(f"Maximum number of values per parameter: {stats_dict['max']:.0f}")
        st.markdown(f"Minimum number of values per parameter: {stats_dict['min']:.0f}")
        st.markdown(f"10 and 90th percentile for value count per parameter: {stats_dict['percentile_10']:.0f}, {stats_dict['percentile_90']:.0f}")
        AgGrid(df)

    par_stats = calc_stats()
    par_stats = filter_stats(par_stats)
    show_result(par_stats)
    
def show_filters(df):
    x = st.session_state.config.key2col()
    station_key = x[cn.STATION_IDENTIFIER_COL]
    par_col = x[cn.PARAMETER_COL]
    lst_stations = list(df[station_key].unique())
    stations = st.sidebar.multiselect("Station", options=lst_stations)
    date_from = st.sidebar.date_input("Date from")
    date_to = st.sidebar.date_input("Date to")
    parameter_options = st.session_state.config.key2par().values()
    columns_options = st.session_state.config.key2col().values()
    parameters = st.sidebar.multiselect("Parameters", parameter_options)
    columns = st.sidebar.multiselect("Columns", columns_options)
    if len(columns)>0:
        columns_options = columns
    order_by_cols = st.sidebar.multiselect("Order by", columns_options)
    df = st.session_state.config.row_value_df
    df = df[df[par_col].isin(parameters)]
    if len(columns)>0:
        df = df[columns]
    if len(order_by_cols)>0:
        df.sort_values(by=order_by_cols, inplace=True)
    ##df_sample = df[st.session_state.config.get_parameter_detail_form_columns()]
    #st.markdown(f"Station: {df.iloc[0][station_key]}")
    #st.markdown(f"Sample date: {df.iloc[0][sample_key]}")

    AgGrid(df.head(5000))

def show_detail():
    df = st.session_state.config.row_value_df
    par_col = st.session_state.config.key2col()[cn.PARAMETER_COL]
    station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
    date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
    par_list = list(st.session_state.config.parameter_map_df.index)
    parameter = st.sidebar.selectbox("Parameter", par_list)
    stations_list = ['Select a station']
    stations_list.extend(list(df[station_col].unique()))
    station = st.sidebar.selectbox("Station", options=stations_list)
    
    cols = st.sidebar.columns((2,3))
    with cols[0]:
        operator = st.selectbox('Value', ['','>', '<', '>=','<=', '=='])
    with cols[1]:
        if operator != '':
            value = st.number_input('', 0.0000)
    field_list = st.session_state.config.column_map_df.index
    fields = st.sidebar.multiselect("⚙️ Show columns", field_list)
    standards =  st.session_state.config.get_standards(parameter)

    df = df[df[par_col]==parameter]
    if stations_list.index(station) > 0:
        df = df[df[station_col]==station]
    value_col = st.session_state.config.key2col()[cn.VALUE_NUM_COL]
    if operator == '>':
        df = df[df[value_col] > value]
    elif operator == '<':
        df = df[df[value_col] < value]
    elif operator == '>=':
        df = df[df[value_col] >= value]
    elif operator == '<=':
        df = df[df[value_col] <= value]
    elif operator == '==':
        df = df[df[value_col] == value]
    
    show_guideline= False
    if len(standards) > 0:
        show_guideline = st.sidebar.checkbox(f"Show guideline ({standards[0]['value']} {standards[0]['unit']})")
        if show_guideline:
            gl_value = standards[0]['value'] / 1000

    title = f"{station}: {parameter}" if station != stations_list[0] else f"{parameter}" 
    
    from_date = df[date_col].min()
    to_date = df[date_col].max()
    num_total = len(df)
    detects = len(df[df[cn.ND_FLAG_COL] == False])
    un_detects = len(df[df[cn.ND_FLAG_COL] == True])
    pct_detects = un_detects / num_total if num_total > 0 else 0
    date_fmt = st.session_state.config.date_format
    stations = len(df[station_col].value_counts())
    st.write(f"#### {title}")
    with st.expander("Summnary"):
        if show_guideline: 
            exc_df = df[df[cn.VALUE_NUM_COL] >= gl_value]
            st.markdown(f"{num_total} measured values, {len(exc_df)} exceedances ({len(exc_df) / len(df): .1%})")
        else:
            st.markdown(f"{num_total} measured values")
        st.markdown(f"{detects} detects and {un_detects} undetects ({pct_detects:.1%})")
        st.markdown(f"From *{from_date.strftime(date_fmt)}* to *{to_date.strftime(date_fmt)}*")
        st.markdown(f"Measured at {stations} stations")
    
    if fields != []:
        df = df[fields]
        if show_guideline:
            df[standards[0]['name']] = gl_value
    AgGrid((df))

def show_menu(td: dict):
    global texts_dict
    menu_options = td['menu_options']
    sel_option = st.sidebar.selectbox("Options", menu_options)
    if sel_option == td['menu_options'][0]:
        st.markdown("### Parameters summary")
        show_summary()
    elif sel_option == td['menu_options'][1]:
        show_detail()
    
    

    
