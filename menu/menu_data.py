from argparse import _StoreFalseAction
from email.utils import collapse_rfc2231_value
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd

import const as cn
import helper
from query import qry
import proj.database as db
from datetime import datetime
from plots.map import Map
from plots.time_series import Time_series

project = {}
lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


def show_sample():
    def pivot_station_table(data):
        df = pd.DataFrame({'field':[], 'value':[]})
        cols = data.columns
        for col in cols:
            if col != 'id':
                field = {'field': col, 'value': str(data.iloc[0][col])}
                df=df.append(field, ignore_index=True)
        return df

    station_table_height = 300
    observations_table_height = 500
    map_width=400

    station_id = helper.get_station(default = 0, filter='')
    date = helper.get_date(station_id=station_id, default = None)
    sample_number = project.get_sample_number(date, station_id)
    st.markdown(F"#### Station")
    settings = {'height':station_table_height, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
    station_df = st.session_state.project.get_station_df(station_id)
    station_pivot_df = pivot_station_table(station_df)
    settings['update_mode'] = GridUpdateMode.NO_UPDATE
    # station_df.drop('id', axis=1)
    col1, col2 = st.columns(2)
    with col1:
        helper.show_table(station_pivot_df,[], settings)
    with col2:
        cfg={'extent':7000, 'long': 'longitude', 'lat': 'latitude', 'plot_width':map_width, 'plot_height': station_table_height, 'symbol_size': 12,'fill_colors':['red'], 'fill_alpha': 0.6}
        map = Map(station_df, cfg)
        p = map.get_plot()
        st.bokeh_chart(p)

    sampling_date = datetime.strftime(date, st.session_state.project.date_format)
    st.markdown(f"#### Observations (sampling date: {sampling_date})")
    observation_df =  st.session_state.project.sample_observations(sample_number)
    
    settings['height'] = observations_table_height
    show_observations_grid(sample_number, settings)


def show_observations_grid(sample_number: str, settings:dict, cols:list=[]):
    def filter_parameter_group(df):
        filtered_df = df
        par_meta_data_fields = project.get_parameter_list(cn.ParTypes.PARAMETER.value)
        if 'group2' in par_meta_data_fields:
            cols = st.columns(4)
            with cols[0]:
                options = ['Select parameter group'] + project.parameter_group1
                g1 = st.selectbox('Parameter group1', options=options)
                if g1 != options[0]:
                    filtered_df = df[df['group1'] == g1]
            with cols[1]:
                options = ['Select parameter group'] + project.parameter_group2
                g2 = st.selectbox('Parameter group2', options=options)
                if g2 != options[0]:
                    filtered_df = filtered_df[filtered_df['group2'] == g2]
        elif 'group1' in par_meta_data_fields:
            options = ['Select parameter group'] + project.parameter_group1
            g1 = st.selectbox('Parameter group1', options=options)
            if g1 != options[0]:
                filtered_df = df[df['group1'] == g1]
        return filtered_df

    df = project.sample_observations(sample_number)
    st.markdown(f"#### Observations ({len(df)})")
    df = filter_parameter_group(df)
    cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
    cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
    settings['update_mode'] = GridUpdateMode.NO_UPDATE
    grid_response = helper.show_table(df,cols, settings)


def show_stations():
    df = project.station_data()
    st.markdown(F"#### Stations ({len(df)})")
    settings = {'height':400, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
    cols=[]
    grid_response = helper.show_table(df,cols, settings)
    with st.expander('Info'):
        st.markdown('Select a station to see more details on sampling events at this station')

    if len(grid_response) > 0:
        station_id = grid_response.iloc[0]['id']
        df = project.station_samples(station_id)
        st.markdown(f"#### Samples ({len(df)})")
        grid_response = helper.show_table(df,cols, settings)
        with st.expander('Info'):
            st.markdown('Select a sample event to see more details on the analysis')

    if len(grid_response) > 0:
        sample_number = grid_response.iloc[0]['sample_number']
        show_observations_grid(sample_number, settings, cols)


def show_parameters():
    obs_filter = helper.get_filter(['stations', 'sampling_date'])
    st.markdown(f"#### Parameters")
    df = project.parameter_data()
    cols = []
    cols.append({'name': 'id', 'type': 'int', 'precision': 0, 'hide':True})
    settings = {'height':400, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
    grid_response = helper.show_table(df,cols, settings)

    if len(grid_response)>0:
        st.markdown(F"#### Observations")
        parameter_id = grid_response.iloc[0]['id']
        df = project.parameter_observations(parameter_id, obs_filter)
        cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'is_non_detect', 'type': 'int', 'precision': 0, 'hide':True})
        grid_response = helper.show_table(df,cols, settings)
        if len(grid_response)>0:
            cfg= st.session_state.user.read_config(cn.TIME_SERIES_ID,'default')
            cfg['parameters'] = [parameter_id]
            cfg['legend_items'] = [grid_response.iloc[0]['parameter_name']]
            cfg['stations'] = [grid_response.iloc[0]['station_id']]
            cfg['plot_width'] = 800
            cfg['plot_height'] = 300
            df_filtered = df[(df['station_id']==grid_response.iloc[0]['station_id'])]
            plot = Time_series(df_filtered, cfg).get_plot()
            st.bokeh_chart(plot)

    if len(grid_response)>0:
        station_id = grid_response.iloc[0]['station_id']
        sample_date = grid_response.iloc[0]['sampling_date']
        sample_date = datetime.strptime(sample_date, '%Y-%m-%dT%H:%M:%S')
        sample_number = project.get_sample_number(sample_date, station_id)
        cols.append({'name': 'station_id', 'type': 'int', 'precision': 0, 'hide':True})
        cols.append({'name': 'parameter_id', 'type': 'int', 'precision': 0, 'hide':True})
        settings['update_mode'] = GridUpdateMode.NO_UPDATE

        st.markdown(f"#### {lang['sample']}")
        st.markdown(f"lang['station']: *{project.stations_df.loc[station_id]['station_identifier']}*<br>{lang['sampling_date']}: *{sample_date.strftime(project.date_format)}*<br>sample_number: *{sample_number}*", unsafe_allow_html=True)
        show_observations_grid(sample_number, settings, cols)


def show_menu():
    global project 
    set_lang()

    project = st.session_state.project
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    MENU_FUNCTIONS = [show_stations, show_sample, show_parameters]
    id = MENU_OPTIONS.index(menu_action)
    MENU_FUNCTIONS[id]()
