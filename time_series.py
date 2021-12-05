from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead
from bokeh.core.enums import MarkerType, LineDash
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


def draw_markers(p, df):
    return p


def show_save_file_button(p):
    if st.button("Save png file"):
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

def show_time_series(data):
    p = figure(width=800, height=int(800 * cn.sin60), 
        y_range=(-figure_padding_bottom, int((200+gap+figure_padding_top) * cn.sin60)), 
        tools=[HoverTool()],
        tooltips="X: @x <br>Y: @y",
        x_range=(-figure_padding_left, 200 + gap + figure_padding_right))
    p = draw_markers(p, data)
    st.bokeh_chart(p)
    show_save_file_button(p)
    
        
def show_settings(df:pd.DataFrame):
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
    df = st.session_state.config.row_value_df
    menu_options = texts_dict["menu_options"]
    parameter_options = list(st.session_state.config.parameter_map_df.index)
    parameter_options.sort()
    menu_action = st.sidebar.selectbox('Options', menu_options)
    sel_parameter = st.sidebar.selectbox('Parameter', parameter_options)
    if menu_action == menu_options[0]:
        show_time_series(df)
    elif menu_action == menu_options[1]:
        show_settings(df)
    

