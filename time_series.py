from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead
from bokeh.palettes import Category10,Category20b
from bokeh.core.enums import MarkerType, LineDash
import helper
import const as cn
import itertools  


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




def draw_markers(p, df):
    return p

def show_save_file_button(p, key):
    if st.button("Save png file", key = key):
        filename = helper.get_random_filename('piper','png')
        export_png(p, filename=filename)
        helper.flash_text(f"the Piper plot has been saved to **{filename}** and is ready for download", 'info')
        with open(filename, "rb") as file:
            btn = st.download_button(
                label="Download image",
                data=file,
                file_name=filename,
                mime="image/png"
            )

def show_time_series_multi_parameters():
    def get_filter(df):
        parameter_options = list(st.session_state.config.parameter_map_df.index)
        parameter_options.sort()
        sel_parameters = st.sidebar.multiselect('Parameter', parameter_options, parameter_options[0])
        x = st.session_state.config.key2col()
        station_col = x[cn.STATION_IDENTIFIER_COL]
        par_col = x[cn.PARAMETER_COL]
        value_col = x[cn.VALUE_NUM_COL]
        date_col = x[cn.SAMPLE_DATE_COL]
        lst_stations = list(df[station_col].unique())
        sel_stations = st.sidebar.multiselect('Station', lst_stations, lst_stations[0])
        return sel_parameters, sel_stations, station_col, date_col, par_col, value_col

    def color_gen():
        yield from itertools.cycle(Category10[10])

    data = st.session_state.config.row_value_df
    sel_parameters, sel_stations, station_col, date_col, par_col, value_col = get_filter(data)
    
    for station in sel_stations:
        station_data = data[data[station_col] == station].sort_values(date_col)
        p = figure(title= station,x_axis_type="datetime", toolbar_location="above", tools="hover", 
            plot_width = 800, plot_height=350)
        p.title.align = "center"
        color = color_gen()
        i=0
        lines = []
        legend_items = []
        for par in sel_parameters:
            df = station_data[station_data[par_col] == par]
            x = p.line(date_col, value_col, line_color=next(color), line_width = 3, source=df)
            legend_items.append((par,[x]))
            i+=1

        legend = Legend(items=legend_items, 
            location=(0, 0), click_policy="hide")
        p.add_layout(legend, 'right')

        st.bokeh_chart(p)
        show_save_file_button(p,station)
    
        
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


def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    if menu_action == menu_options[0]:
        show_time_series_multi_parameters()
    elif menu_action == menu_options[1]:
        show_settings()
    

