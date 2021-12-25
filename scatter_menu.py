from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
import itertools  
from st_aggrid import AgGrid
from scatter import Scatter
import helper
import const as cn

gap = 20
figure_padding_left = 10
figure_padding_right = 10
figure_padding_top = 10
figure_padding_bottom = 20
marker_size = 10
tick_len = 2
grid_color = 'silver'
line_color = 'black'
grid_line_pattern = 'dashed'
tick_label_font_size = 8
axis_title_font_size = 10
grid_line_pattern = 'dotted'
legend_location = "top_right"
arrow_length = 5
arrow_size = 5
image_file_format = 'png'

group_by_options = ['None', 'Station', 'Year']
legend_options = ['None', 'Station', 'Year']


def get_parameters(df:pd.DataFrame):
    parameter_options = list(st.session_state.config._parameter_map_df.index)
    parameter_options.sort()
    x_par = st.sidebar.selectbox('X-parameter', parameter_options, 0)
    y_par = st.sidebar.selectbox('Y-Parameter', parameter_options, 1)
    
    return x_par, y_par

def get_filter(df:pd.DataFrame):
    x = st.session_state.config.key2col()
    station_col = x[cn.STATION_IDENTIFIER_COL]
    with st.sidebar.expander('🔎 Filter'):
        lst_stations = list(df[station_col].unique())
        sel_stations = st.multiselect('Station', lst_stations, lst_stations[0])
    
    if len(sel_stations)> 0:
        df = df[df[station_col].isin(sel_stations)]
    else:
        sel_stations = lst_stations
    return df, sel_stations


def show_scatter_plot(data, cfg, sel_stations):

    def get_settings(cfg):
        with st.sidebar.expander('⚙️ Settings'):
            cfg['group_plot_by'] = st.selectbox('Group plots by', group_by_options)
            cfg['legend'] = st.selectbox('Legend', legend_options)
            cfg['symbol_size'] = st.number_input('Marker size', min_value=1, max_value=50, step=1, value=int(cfg['symbol_size']))
            cfg['fill_alpha'] = st.number_input('Marker alpha', min_value=0.0,max_value=1.0,step=0.1, value=cfg['fill_alpha'])

            cfg['y_axis_auto'] = st.checkbox("Y axis auto", True)
            if not cfg['y_axis_auto']:
                cols = st.columns(2)
                with cols[0]:
                    cfg['x_axis_min'] = st.text_input("X-axis Start")
                    cfg['y_axis_min'] = st.text_input("Y-axis Start")
                with cols[1]:
                    cfg['x_axis_max'] = st.text_input("X-axis End")
                    cfg['y_axis_max'] = st.text_input("Y-axis End")
            cfg['show_h_line'] = st.checkbox("Show horizontal line", False)
            if cfg['show_h_line']:
                cfg['h_line'] = st.number_input("y axis intercept", 0)
            cfg['show_v_line'] = st.checkbox("Show vertical line", False)
            if cfg['show_v_line']:
                cfg['v_line'] = st.number_input("x axis intercept", 0)
            cfg['show_corr_line'] = st.checkbox("Show correlation", False)
        return cfg

    cfg = get_settings(cfg)
    df = st.session_state.config.row_sample_df
    if cfg['group_plot_by'] == group_by_options[0]:
        scatter = Scatter(df, cfg)
        plot, df_stats = scatter.get_plot()
        st.bokeh_chart(plot)
        if cfg['show_corr_line']:
            with st.expander("Stats"):
                AgGrid(df_stats)
    else:
        # e.g. group by station: 1 plot per station
        pass

def show_settings():
    def show_axis_settings():
        
        with st.form("my_form1"):
            col1, col2 = st.columns(2)
            with col1:            
                show_gridlines = st.checkbox("Show Gridlines")
                marker_column = st.selectbox("Grid line pattern", helper.get_parameter_columns('station'))
                marker_proportional = st.selectbox("Size or color proportional to value", ['None', 'Size', 'Color'])
            with col2:            
                grid_line_pattern = st.selectbox("Grid line pattern", list(LineDash))
                diff_marker = st.checkbox("Use distinct marker for each group")

            st.markdown("---")
            if st.form_submit_button("Submit"):
                st.markdown("slider", "checkbox", show_gridlines)


    menu_options = ['Axis Settings', 'Markers']
    menu_action = st.sidebar.selectbox("Setting",menu_options)
    if menu_action == menu_options[0]:
        show_axis_settings()

def verify_columns(data, cfg):
    data = data.rename(columns={cfg['x_par']: cfg['x_par'].replace('-','_')})
    data = data.rename(columns={cfg['y_par']: cfg['y_par'].replace('-','_')})
    cfg['x_par'] = cfg['x_par'].replace('-','_')
    cfg['y_par'] = cfg['y_par'].replace('-','_')
    return data

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    data = st.session_state.config.row_sample_df
    cfg = cn.scatter_cfg
    cfg['x_par'], cfg['y_par'] = get_parameters(data)
    data, sel_stations = get_filter(data)
    # data = verify_columns(data, cfg)
    if menu_action == menu_options[0]:
        show_scatter_plot(data, cfg, sel_stations)
    elif menu_action == menu_options[1]:
        pass # correlation matrix to come
    

