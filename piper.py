from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead
from bokeh.core.enums import MarkerType, LineDash
from streamlit.delta_generator import MAX_DELTA_BYTES
from datetime import datetime, timedelta
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


def get_tranformed_data(data):
    def transform_to_xy(df, type):
        if type == 'cations':
            pct_array = df[['ca_pct', 'na_pct', 'mg_pct']].to_numpy()
            offset = 0
        else:
            pct_array = df[['alk_pct', 'cl_pct', 'so4_pct']].to_numpy()
            offset = 100 + gap
        df_xy = pd.DataFrame()
        x = 0
        y = 0
        i = 0
        for row in pct_array:
            if row[0] == 100:
                x = 0
                y = 0
            elif row[1] == 100:
                x = 100
                y = 0
            elif row[2] == 100:
                x = 50
                y = 100 * cn.sin60
            else:
                x = row[1] / (row[0] + row[1]) * 100
                # find linear equation mx + q = y
                if x != 50:
                    m = 100 / (50 - x)
                    q = -(m * x)
                    x = (row[2] - q) / m
                y = cn.sin60 * row[2]

            df_xy = df_xy.append({'x': x + offset, 'y': y, 'type': type[0:1]}, ignore_index=True)
            i += 1

        df_xy = df_xy.join(df)
        return df_xy

    def projected_point(anions, cations):
        # ax! = ax! + 110
        #
        # m! = TAN60
        # Q1! = cy! - m! * cx!
        # Q2! = ay! + m! * ax!
        # prx! = (Q2! - Q1!) / (2 * m!)
        # pry! = TAN60 * prx! + Q1!

        df_xy = pd.DataFrame()
        for i in range(0, len(anions)):     
            m = cn.tan60
            q1 = cations.iloc[i]['y'] - (m * cations.iloc[i]['x'])
            q2 = anions.iloc[i]['y'] + (m * anions.iloc[i]['x'])
            
            prx = (q2 - q1) / (2 * m)
            pry = m * prx + q1
            df_xy = df_xy.append({'x': prx, 'y': pry,'type': 'p'}, ignore_index=True)
        return df_xy

    cations_df = transform_to_xy(data, 'cations')
    anions_df = transform_to_xy(data, 'anions')
    projected_df = projected_point(anions_df, cations_df)
    projected_df = projected_df.join(data)
    df_xy = pd.concat([cations_df, anions_df, projected_df], ignore_index=True)
    return df_xy


def draw_triangles(p):
    x1 = [0, 100, 50, 0]
    y1 = [0, 0, cn.sin60*100, 0]

    x2 = [100+gap, 200+gap, 150+gap, 100+gap]
    y2 = [0, 0, cn.sin60*100, 0]

    x4 = [100+gap/2, 50+gap/2, 100+gap/2, 150+gap/2, 100+gap/2]
    y4 = [cn.sin60 * gap, cn.sin60*(100 + gap), cn.sin60*(200 + gap), cn.sin60 * (100 + gap), cn.sin60*gap]
    p.axis.visible = False
    p.grid.visible = False

    p.line(x1, y1, line_width=1, color=line_color)
    p.line(x2, y2, line_width=1, color=line_color)
    p.line(x4, y4, line_width=1, color=line_color)

    return p


def draw_axis(p):
    def draw_xaxis_base(offset:bool, p):
        y = [0,-tick_len * cn.sin60]
        for i in range(1,5):
            delta = (100+gap) if offset else 0
            if offset:
                x = [i*20+delta, i*20 - tick_len * cn.cos60 + delta]
            else:
                x = [i*20+delta, i*20 + tick_len * cn.cos60 + delta]
            p.line(x, y, line_width=1, color=line_color) 
            text = str(i*20) if offset else str(100-i*20)
            tick_label = Label(x=x[1]-2, y=y[1]-6,text_font_size=f"{tick_label_font_size}pt",
                 text=text, render_mode='css')
            p.add_layout(tick_label)
        return p

    def draw_triangle_left(p, offset:bool):
        delta = (100+gap) if offset else 0
        for i in range(1,5):
            x_tick = [delta + i * 10, delta + i * 10 - tick_len] 
            y_tick = [i * 20 * cn.sin60, i * 20 * cn.sin60]
            p.line(x_tick, y_tick, line_width=1, color=line_color)  
            if not offset:
                y = y_tick[1] - 3
                x = x_tick[1] - 5
                tick_label = Label(x=x, y=y,text_font_size=f"{tick_label_font_size}pt",
                    text=str(i*20), render_mode='css')
                p.add_layout(tick_label)
        return p

    def draw_triangle_right(p, offset:bool):
        delta = (100+gap) if offset else 0
        for i in range(1,5):
            x_tick = [delta + 100 - i * 10, delta + 100 - i * 10 + tick_len ] 
            y_tick = [i * 20 * cn.sin60, i*20 * cn.sin60]
            p.line(x_tick, y_tick, line_width=1, color=line_color)  
            if offset:
                y = y_tick[1] - 3
                x = x_tick[1] + 1
                tick_label = Label(x=x, y=y,text_font_size=f"{tick_label_font_size}pt",
                    text=str(i*20), render_mode='css')
                p.add_layout(tick_label)
        return p

    def draw_diamond_ul(p):
        for i in range(1, 5):
            x_tick = [50 + gap/2 + i*10, 50 + gap/2 + i*10 - tick_len * cn.cos60]
            y_tick = [(100 + gap + i * 20) * cn.sin60, (100 + gap + i * 20) * cn.sin60 + tick_len * cn.sin60]
            p.line(x_tick, y_tick, line_width=1, color=line_color)  
            y = y_tick[1] - 2
            x = x_tick[1] - 5
            tick_label = Label(x=x, y=y, text_font_size=f"{tick_label_font_size}pt",
                text=str(i*20), render_mode='css')
            p.add_layout(tick_label)
        return p
    
    def draw_diamond_ur(p):
        for i in range(1, 5):
            x_tick = [100 + gap/2 + i*10, 100 + gap/2 + i*10 + tick_len * cn.cos60]
            y_tick = [(200 + gap - i * 20) * cn.sin60, (200 + gap - i * 20) * cn.sin60 + tick_len * cn.sin60]
            p.line(x_tick, y_tick, line_width=1, color=line_color)
            y = y_tick[1] - 2
            x = x_tick[1] + 1
            tick_label = Label(x=x, y=y, text_font_size=f"{tick_label_font_size}pt",
                               text=str(100-i*20), render_mode='css')
            p.add_layout(tick_label)
        return p

    def draw_grids(p):        
        def draw_triangle_grids(offset: bool):
            delta = (100+gap) if offset else 0
            for i in range(1,5):
                # left-right
                x = [i*10+delta,100 - i*10 + delta]
                y = [i*20 * cn.sin60, i*20 * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # horizontal
                x = [i*20+delta,50 + i*10 + delta]
                y = [0,(100 - i*20) * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # right-left
                x = [i*20+delta,i*10 + delta]
                y = [0, i*20 * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
            return p

        def draw_diamond_grid():
            for i in range(1,5):   
                # diamond left-right
                x = [50 + gap/2 + i*10, 100 + gap/2 + i*10 ]
                y = [(100 + gap + i * 20) * cn.sin60, (gap + i * 20) * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # diamond right-left
                x = [100 + gap/2 + i*10, 50 + gap/2 + i*10 ]
                y = [(200 + gap - i * 20) * cn.sin60, (100 + gap - i * 20) * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern)  
                # diamond horizontal top
                x = [50 + gap/2 + i*10, 100 + gap/2 + 50 - i*10 ]
                y = [(100 + gap + i * 20) * cn.sin60, (100 + gap + i * 20) * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # diamond horizontal bottom
                x = [100 + gap/2 + i*10, 100 + gap/2 - i*10]
                y = [(gap + i * 20) * cn.sin60, (gap + i * 20) * cn.sin60]
                p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
            # middle line
            x = [50 + gap/2, 100 + gap + 50 -gap/2]
            y = [(100 + gap)*cn.sin60,(100 + gap)*cn.sin60]
            p.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
            return p
        
        def draw_axis_titles(p):
            def draw_ca_title(p):
                x = 50 - 3
                y = 0 - 3 - axis_title_font_size 
                xa = [x - 2, x - 2 - arrow_size]
                ya = [y + 2.5, y + arrow_size ]
                title = 'Ca++'

                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold')
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=arrow_size), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                return p
            
            def draw_cl_title(p):
                x = 100 + gap + 50 - 3
                y = 0 - 3 - axis_title_font_size 
                xa = [x + 7, x + 11]
                ya = [y + 2.5, y + 2 ]
                title = 'Cl-'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold')
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                return p
            
            def draw_mg_title(p):
                x = 12
                y = 44 - axis_title_font_size + 3
                #p.circle(x=x,y=y)
                xa = [x + 9 * cn.cos60, x + 9 * cn.cos60 + 4 * cn.cos60]
                ya = [y + 14 * cn.sin60, y + 14 * cn.sin60 + 4 * cn.sin60 ]

                title = 'Mg++'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = 60.5, # not sure why 60 gives the wrong angle
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            
            
            def draw_SO4_title(p):
                x = 200 + gap - 25 - 13 * cn.cos60 + 14
                y = 50 * cn.sin60 - axis_title_font_size + 15*cn.sin60
                #p.circle(x=x,y=y)
                xa = [x + 2 * cn.cos60, x + 2 * cn.cos60 - 4 * cn.cos60]
                ya = [y + 2 * cn.sin60, y + 2 * cn.sin60 + 4 * cn.sin60 ]

                title = 'SO4--'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = -60.5, # not sure why 60 gives the wrong angle
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            
            def draw_cl_so4_title(p):
                x = 50 + gap/2 + 20 - 10
                y = (100 + gap + 40)*cn.sin60

                xa = [x + 23 * cn.cos60 - 2 * cn.cos60, x + 25 * cn.cos60 - 2 * cn.cos60 + (arrow_length * cn.cos60)]
                ya = [y + 23 * cn.sin60 + 2*cn.sin60, y + 25 * cn.sin60 + 2*cn.sin60 + (arrow_length * cn.sin60)]

                title = 'Cl- + SO4--'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = 60, # not sure why 60 gives the wrong angle
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            
            def draw_ca_mg_title(p):
                x = 100 + gap + 50 - 33
                y = (100 + gap + 70) * cn.sin60

                xa = [x + 30 * cn.cos60 + 3 * cn.cos60, x + 30 * cn.cos60 + 3 * cn.cos60 + (arrow_length * cn.cos60)]
                ya = [y - 30 * cn.sin60 + 3 * cn.sin60, y - 30 * cn.sin60 + 3 * cn.sin60 - (arrow_length * cn.sin60)]

                title = 'Ca++ + Mg++'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = -60, 
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            
            def draw_HCO3_CO3_title(p):
                x = 100 + gap / 2 + 23
                y = gap + 20

                xa = [x - 3 , x - 3 - (arrow_length * cn.cos60)]
                ya = [y, y - (arrow_length * cn.sin60)]

                title = 'HCO3- + CO3--'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = 60, 
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            
            def draw_Na_K_title(p):
                x = 100 + gap/2 - 30 - 9
                y = (80-3) * cn.sin60

                xa = [x + (19 + 6) * cn.cos60, x + (19 + 6) * cn.cos60 + (arrow_length * cn.cos60)]
                ya = [y - 19  * cn.sin60, y - 19  *cn.sin60 - (arrow_length * cn.sin60)]

                title = 'Na+ + K+'
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{axis_title_font_size}pt",
                    text=title, text_font_style ='bold',
                    angle = -60, 
                    angle_units="deg")
                p.add_layout(tick_label)
                p.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                    x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                return p
            

            p = draw_ca_title(p)
            p = draw_cl_title(p)
            p = draw_mg_title(p)
            p = draw_SO4_title(p)
            p = draw_cl_so4_title(p)
            p = draw_ca_mg_title(p)
            p = draw_HCO3_CO3_title(p)
            p = draw_Na_K_title(p)
            
            return p

        def draw_main_labels(p,titles,offset:bool):
            delta = 100 + gap if offset else 0
            # Ca/Alk
            if not offset:
                x = 0 - axis_title_font_size * .6 + delta
            else:
                x = delta
            y = 0 - axis_title_font_size * .8
            tick_label = Label(x=x, y=y,
                text_font_size=f"{axis_title_font_size}pt",
                text=titles[0], text_font_style ='bold')
            p.add_layout(tick_label)
            
            # Na+K/Cl: todo: find out how the calculate the length of the text
            if not offset:
                x = 100 - 6 - len(titles[1]) + delta
            else:
                x = 100 + delta
            y = 0 - axis_title_font_size * .8
            tick_label = Label(x=x, y=y,text_font_size=f"{axis_title_font_size}pt",
                text=titles[1], text_font_style ='bold')
            p.add_layout(tick_label)

            # Mg/SO4
            x = 50  + delta
            y = 100 * cn.sin60 + 2   
            tick_label = Label(x=x, y=y,text_font_size=f"{axis_title_font_size}pt",
                text=titles[2], text_font_style ='bold')
            p.add_layout(tick_label)
            return p

        p = draw_triangle_grids(offset=False)
        p = draw_triangle_grids(offset=True)
        p = draw_diamond_grid()
        p = draw_axis_titles(p)
        p.legend.click_policy="mute"
        return p

    p = draw_xaxis_base(False, p)
    p = draw_xaxis_base(True, p)
    p = draw_triangle_left(p, False)
    p = draw_triangle_left(p, True)
    p = draw_triangle_right(p, False)
    p = draw_triangle_right(p, True)
    p = draw_diamond_ul(p)
    p = draw_diamond_ur(p)

    p = draw_grids(p)
    return p


def draw_markers(p, df):
    i = 0
    station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
    for station in df[station_col].dropna().unique():
        df_filtered = df[df[station_col] == station]
        colors = ['red','green','blue','orange','yellow','red','green','blue','orange','yellow','red','green','blue','orange','yellow']
        markers = ['circle','rect','triangle','cross','circle','rect','triangle','cross''circle','rect','triangle','cross']
        #for index,row in df_filtered.iterrows():
        if markers[i]=='circle':
            p.circle(df_filtered['x'], df_filtered['y'], legend_label=station, size=marker_size, color=colors[i], alpha=0.8)
        elif markers[i]=='rect':
            p.square(df_filtered['x'], df_filtered['y'], legend_label=station,size=marker_size, color=colors[i], alpha=0.8)
        elif markers[i]=='triangle':
            p.triangle(df_filtered['x'], df_filtered['y'], legend_label=station,size=marker_size, color=colors[i], alpha=0.8)
        elif markers[i]=='cross':
            p.cross(df_filtered['x'], df_filtered['y'], legend_label=station,size=marker_size, color=colors[i], alpha=0.8)
        i+=1
        if i == len(markers):
            i=0
        p.legend.location = legend_location
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


def show_piper(data):
    p = figure(width=800, height=int(800 * cn.sin60), 
        y_range=(-figure_padding_bottom, int((200+gap+figure_padding_top) * cn.sin60)), 
        tools=[HoverTool()],
        tooltips="X: @x <br>Y: @y",
        x_range=(-figure_padding_left, 200 + gap + figure_padding_right))
    p = draw_triangles(p)
    p = draw_axis(p)
    data_transformed = get_tranformed_data(data)
    p = draw_markers(p, data_transformed)
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

def filter(df: pd.DataFrame):
    st.sidebar.markdown("🔎 Filter")
    station_col = st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]
    station_options = st.session_state.config.get_station_list()
    sel_stations = st.sidebar.multiselect("Stations", station_options)
    if st.session_state.config.col_is_mapped(cn.SAMPLE_DATE_COL):
        date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
        df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='ignore')
        min_date = df[date_col].min().to_pydatetime().date()
        max_date = df[date_col].max().to_pydatetime().date()
        
        from_date = st.sidebar.date_input("From date", min_date)
        to_date = st.sidebar.date_input("From date", max_date)
        if (from_date != min_date) or (to_date != max_date):
            df = df[(df[date_col].dt.date >= from_date) & (df[date_col].dt.date < to_date)]

    if len(sel_stations)>0:
        df = df[df[station_col].isin(sel_stations)]
    return df

def show_menu(texts_dict:dict):
    menu_options = texts_dict["menu_options"]
    menu_action = st.sidebar.selectbox('Options', menu_options)
    data = filter(st.session_state.config.row_sample_df)
    if menu_action == menu_options[0]:
        show_piper(data)
    elif menu_action == menu_options[1]:
        show_settings(data)
    

