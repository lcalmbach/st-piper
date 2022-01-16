import streamlit as st
import pandas as pd
import const as cn
from st_aggrid import AgGrid
# import numpy as np
import helper
from histogram import Histogram
from time_series import Time_series

texts_dict = ""

def show_summary():
    def calc_stats(df):
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
        with st.sidebar.expander('🔎 Filter'):
            sel_stations = st.multiselect('Stations', st.session_state.config.get_station_list())
            if len(sel_stations) > 0:
                df = df[df[st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]].isin(sel_stations)]
            if st.session_state.config.col_is_mapped(cn.CATEGORY_COL):
                par_cat_col = st.session_state.config.key2col()[cn.CATEGORY_COL]
                lst_parameter_categories = ['Select a category']
                lst_parameter_categories.extend(list(df[par_cat_col].unique()))
                sel_parameter_category = st.selectbox('Parameter category', lst_parameter_categories)
                if sel_parameter_category != lst_parameter_categories[0]:
                    df = df[df[par_cat_col] == sel_parameter_category]
        return df

    def show_result(df):
        with st.expander("Summary"):
            stats_dict = get_count_stats(df)
            st.markdown(f"Number of parameters: {len(df)}")
            st.markdown(f"Maximum number of observations per parameter: {stats_dict['max']:.0f}")
            st.markdown(f"Minimum number of observations per parameter: {stats_dict['min']:.0f}")
            st.markdown(f"10th percentile for observation count per parameter = {stats_dict['percentile_10']:.0f} and 90th percentile = {stats_dict['percentile_90']:.0f}")
        AgGrid(df)

    filtered_data = filter_stats(st.session_state.config.row_value_df)
    par_stats = calc_stats(filtered_data)
    show_result(par_stats)

def show_filters(df):
    x = st.session_state.config.key2col()
    station_key = x[cn.STATION_IDENTIFIER_COL]
    par_col = x[cn.PARAMETER_COL]
    lst_stations = list(df[station_key].unique())
    with st.sidebar.expander("🔎 Filter"):
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

def show_plots(df, parameter, show_histo, show_time_series):
    def get_histo_plot():
        cfg = cn.histogram_cfg
        cfg['parameter'] = parameter
        cfg['value_col'] = st.session_state.config.value_col
        cfg['plot_width'] = cn.DEFAULT_PLOT_WIDTH_S
        cfg['plot_height'] = cn.DEFAULT_PLOT_HEIGHT_S
        cfg['x_min'] = df[cfg['value_col']].min()
        cfg['x_max'] = df[cfg['value_col']].max()
        histo = Histogram(df, cfg)
        return histo.get_plot()
        
    
    def get_time_series_plot():
        cfg = cn.time_series_cfg
        cfg['parameter'] = parameter
        cfg['value_col'] = st.session_state.config.value_col
        cfg['plot_width'] = cn.DEFAULT_PLOT_WIDTH_M
        cfg['plot_height'] = cn.DEFAULT_PLOT_HEIGHT_S
        cfg['legend_items'] = [parameter]
        cfg['legend_col'] = st.session_state.config.parameter_col
        
        ts = Time_series(df, cfg)
        return ts.get_plot()

    df = df.sort_values(st.session_state.config.date_col)
    # if show_histo and show_time_series:
    #     cols = st.columns([2,2])
    #     with cols[0]:
    #         st.markdown(f'Time series of {parameter}')
    #         st.bokeh_chart(get_time_series_plot())
    #     with cols[1]:
    #         st.markdown(f'Histogram of {parameter}')
    #         st.bokeh_chart(get_histo_plot())
    if show_histo:
        st.markdown(f'Histogram of {parameter}')
        st.bokeh_chart(get_histo_plot())
    if show_time_series:
        st.markdown(f'Time series of {parameter}')
        st.bokeh_chart(get_time_series_plot())


def show_detail():
    df = st.session_state.config.row_value_df
    par_col = st.session_state.config.key2col()[cn.PARAMETER_COL]
    station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
    date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
    value_col = st.session_state.config.key2col()[cn.VALUE_NUM_COL]
    par_list = list(st.session_state.config.parameter_map_df.index)
    parameter = st.sidebar.selectbox("Parameter", par_list)
    stations_list = ['Select a station']
    with st.sidebar.expander("🔎 Filter"):
        stations_list.extend(list(df[station_col].unique()))
        station = st.selectbox("Station", options=stations_list)
    
        cols_value = st.columns((2,3))
        with cols_value[0]:
            operator = st.selectbox('Value', ['','>', '<', '>=','<=', '=='])
        with cols_value[1]:
            if operator != '':
                value = st.number_input('', 0.0000)
        
        cols_date = st.columns(2)
        date_from, date_to, date_is_filtered = helper.date_filter(df, cols_date)
        
    field_list = st.session_state.config.column_map_df.index
    show_guideline= False
    show_histogram = False
    show_time_series = False
    with st.sidebar.expander("⚙️ Settings"):
        fields = st.multiselect("Show columns", field_list)
        # guideline_options = list(st.session_state.config.guidelines_df['name'])
        # if len(guidelines) > 0:
        #     sel_guideline = st.selectbox(Guideline)
        #     show_guideline = st.checkbox(f"Show guideline ({guidelines[0]['value']} {guidelines[0]['unit']})")
        #     if show_guideline:
        #         gl_value = guidelines[0]['value'] / 1000
        show_histogram = st.checkbox("Show histogram",False)
        show_time_series = False
        if stations_list.index(station) > 0:
            show_time_series = st.checkbox("Show time series",False)

    df = df[df[par_col]==parameter]
    if date_is_filtered:
        df = df[(df[date_col] >= pd.to_datetime(date_from)) & (df[date_col] <= pd.to_datetime(date_to))]
    if stations_list.index(station) > 0:
        df = df[df[station_col]==station]
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
    
    title = f"{station}: {parameter}" if station != stations_list[0] else f"{parameter}" 
    
    num_total = len(df)
    detects = len(df[df[cn.ND_FLAG_COL] == False])
    un_detects = len(df[df[cn.ND_FLAG_COL] == True])
    pct_detects = un_detects / num_total if num_total > 0 else 0
    date_fmt = st.session_state.config.date_format
    stations = len(df[station_col].value_counts())
    st.write(f"#### {title}")
    with st.expander("Summary"):
        if show_guideline: 
            exc_df = df[df[cn.VALUE_NUM_COL] >= gl_value]
            st.markdown(f"{num_total} observations, {len(exc_df)} exceedances ({len(exc_df) / len(df): .1%})")
        else:
            st.markdown(f"{num_total} observations")
        st.markdown(f"{detects} detects and {un_detects} undetects ({pct_detects:.1%})")
        st.markdown(f"From *{date_from.strftime(date_fmt)}* to *{date_to.strftime(date_fmt)}*")
        st.markdown(f"Measured at {stations} stations")
    
    # if fields != []:
    #     df = df[fields]
    #     if show_guideline:
    #         df[standards[0]['name']] = gl_value
    
    AgGrid(df)
    show_plots(df, parameter, show_histogram, show_time_series)

def show_menu(td: dict):
    global texts_dict
    menu_options = td['menu_options']
    sel_option = st.sidebar.selectbox("", menu_options)
    if sel_option == td['menu_options'][0]:
        st.markdown("### Parameters summary")
        show_summary()
    elif sel_option == td['menu_options'][1]:
        show_detail()
