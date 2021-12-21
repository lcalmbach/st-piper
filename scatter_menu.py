from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot
from bokeh.core.enums import MarkerType
from bokeh.transform import factor_mark, factor_cmap
from bokeh.palettes import Category10,Category20b
from bokeh.core.enums import MarkerType, LineDash
import itertools  
from scipy.stats.stats import pearsonr
from st_aggrid import AgGrid

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

    def color_gen():
        yield from itertools.cycle(Category10[10])

    def group_plots(p, cfg):
        pass
    
    def add_correlation(p, data):
        def estimate_coef(x, y):
            # number of observations/points
            n = np.size(x)
            # mean of x and y vector
            m_x = np.mean(x)
            m_y = np.mean(y)
            
            # calculating cross-deviation and deviation about x
            SS_xy = np.sum(y*x) - n*m_y*m_x
            SS_xx = np.sum(x*x) - n*m_x*m_x
        
            # calculating regression coefficients
            b_1 = SS_xy / SS_xx
            b_0 = m_y - b_1*m_x
            return (b_0, b_1)

        df = data.dropna()
        df.columns = ['x','y']
        print(type(df))
        x = helper.nd2numeric(df[['x']])
        y = helper.nd2numeric(df[['y']])
        corr_coeff = estimate_coef(x,y)
        # calculate pearson correlation coefficient 
        r = pearsonr(x, y)
        corr_coeff += r
        x = list(x.reset_index(drop=True))
        x.sort()
        df = pd.DataFrame({'x': [ x[0], x[-1] ]})
        df = df.assign(y = lambda x: corr_coeff[0] + corr_coeff[1] * x['x'])
        plot.line(df['x'], df['y'], line_width=2, color='red')
        return p, corr_coeff
    

    def single_plot(plot, cfg):
        color = color_gen()
        legend_items = []
        clr = next(color)
        # markers are grouped as legends
        if cfg['legend'] == legend_options[0]:
            m = plot.scatter(x=cfg['x_par'], y=cfg['y_par'], source=data, marker=cn.MARKERS[0], 
                size=cfg['symbol_size'], color=clr, alpha=cfg['fill_alpha'])
            #legend_items.append((par,[l,m]))

            legend = Legend(items=legend_items, 
                            location=(0, 0), click_policy="hide")
            plot.add_layout(legend, 'right')
            plot.add_tools(HoverTool(
                tooltips=[
                    ('Station', f"@{st.session_state.config.station_col}"),
                    (cfg['x_par'], f"@{cfg['x_par']}"),
                    # todo: columns must be renamed, since spaces are not allowed here 
                    (cfg['y_par'], f"@{cfg['y_par']}")
                ],
                formatters={
                    '@date': 'datetime', # use 'datetime' formatter for 'date' field
                })
            )
        elif cfg['legend'] == legend_options[1]:
            for station in sel_stations:
                df = data[data[st.session_state.config.station_col] == station]
                clr = next(color)
                m =plot.scatter(x=cfg['x_par'], y=cfg['y_par'], source=df, marker=cn.MARKERS[0], 
                size = cfg['symbol_size'], color=clr, alpha=cfg['fill_alpha'])
                #legend_items.append((par,[l,m]))

                legend = Legend(items=legend_items, 
                                location=(0, 0), click_policy="hide")
                plot.add_layout(legend, 'right')
        if cfg['show_corr_line']:
            plot, corr_coeff = add_correlation(plot,data[[cfg['x_par'], cfg['y_par']]])
            p_val = 0.05
            sign_result = 'Correlation is statisticically significant' if corr_coeff[3] < p_val else 'Correlation is not statisticically significant'
            df = pd.DataFrame({'stat': ['Pearson correlation coefficient', 'associated two-tailed p-value',f'Intepretation (p = {p_val})','Y-axis intercept','slope'],
                               'value': [corr_coeff[2], corr_coeff[3], sign_result, corr_coeff[0], corr_coeff[1]]})
            

        st.bokeh_chart(plot)
        if cfg['show_corr_line']:
            with st.expander("Stats"):
                AgGrid(df)
        # helper.show_save_file_button(p, station)

    plot = figure(toolbar_location="above", 
                tools = [],
                plot_width = 800, 
                plot_height=350)
    plot.title.align = "center"
    plot.yaxis.axis_label = f"{cfg['y_par']} (mg/L)"
    plot.xaxis.axis_label = f"{cfg['x_par']} (mg/L)"
    
    cfg = get_settings(cfg)
    if cfg['group_plot_by'] == group_by_options[0]:
        single_plot(plot, cfg)
    else:
        group_plots(plot,cfg)
    


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
        show_settings()
    

