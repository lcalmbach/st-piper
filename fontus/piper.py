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

class Piper():
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.data = df
        self.cfg = cfg
        self.plot = {}
        
    def get_tranformed_data(self):
        def transform_to_xy(df, type):
            if type == 'cations':
                pct_array = df[self.cfg['cation_cols']].to_numpy()
                offset = 0
            else:
                pct_array = df[self.cfg['anion_cols']].to_numpy()
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

        cations_df = transform_to_xy(self.data, 'cations')
        anions_df = transform_to_xy(self.data, 'anions')
        projected_df = projected_point(anions_df, cations_df)
        projected_df = projected_df.join(self.data)
        df_xy = pd.concat([cations_df, anions_df, projected_df], ignore_index=True)
        return df_xy


    def draw_triangles(self):
        x1 = [0, 100, 50, 0]
        y1 = [0, 0, cn.sin60*100, 0]

        x2 = [100+gap, 200+gap, 150+gap, 100+gap]
        y2 = [0, 0, cn.sin60*100, 0]

        x4 = [100+gap/2, 50+gap/2, 100+gap/2, 150+gap/2, 100+gap/2]
        y4 = [cn.sin60 * gap, cn.sin60*(100 + gap), cn.sin60*(200 + gap), cn.sin60 * (100 + gap), cn.sin60*gap]
        self.plot.axis.visible = False
        self.plot.grid.visible = False

        self.plot.line(x1, y1, line_width=1, color=line_color)
        self.plot.line(x2, y2, line_width=1, color=line_color)
        self.plot.line(x4, y4, line_width=1, color=line_color)


    def draw_axis(self):
        def draw_xaxis_base(offset:bool):
            y = [0,-tick_len * cn.sin60]
            for i in range(1,5):
                delta = (100+gap) if offset else 0
                if offset:
                    x = [i*20+delta, i*20 - tick_len * cn.cos60 + delta]
                else:
                    x = [i*20+delta, i*20 + tick_len * cn.cos60 + delta]
                self.plot.line(x, y, line_width=1, color=line_color) 
                text = str(i*20) if offset else str(100-i*20)
                tick_label = Label(x=x[1]-2, y=y[1]-6,text_font_size=f"{tick_label_font_size}pt",
                    text=text, render_mode='css')
                self.plot.add_layout(tick_label)

        def draw_triangle_left(offset:bool):
            delta = (100+gap) if offset else 0
            for i in range(1,5):
                x_tick = [delta + i * 10, delta + i * 10 - tick_len] 
                y_tick = [i * 20 * cn.sin60, i * 20 * cn.sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                if not offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] - 5
                    tick_label = Label(x=x, y=y,text_font_size=f"{tick_label_font_size}pt",
                        text=str(i*20), render_mode='css')
                    self.plot.add_layout(tick_label)

        def draw_triangle_right(offset:bool):
            delta = (100+gap) if offset else 0
            for i in range(1,5):
                x_tick = [delta + 100 - i * 10, delta + 100 - i * 10 + tick_len ] 
                y_tick = [i * 20 * cn.sin60, i*20 * cn.sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                if offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] + 1
                    tick_label = Label(x=x, y=y,text_font_size=f"{tick_label_font_size}pt",
                        text=str(i*20), render_mode='css')
                    self.plot.add_layout(tick_label)

        def draw_diamond_ul():
            for i in range(1, 5):
                x_tick = [50 + gap/2 + i*10, 50 + gap/2 + i*10 - tick_len * cn.cos60]
                y_tick = [(100 + gap + i * 20) * cn.sin60, (100 + gap + i * 20) * cn.sin60 + tick_len * cn.sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                y = y_tick[1] - 2
                x = x_tick[1] - 5
                tick_label = Label(x=x, y=y, text_font_size=f"{tick_label_font_size}pt",
                    text=str(i*20), render_mode='css')
                self.plot.add_layout(tick_label)
        
        def draw_diamond_ur():
            for i in range(1, 5):
                x_tick = [100 + gap/2 + i*10, 100 + gap/2 + i*10 + tick_len * cn.cos60]
                y_tick = [(200 + gap - i * 20) * cn.sin60, (200 + gap - i * 20) * cn.sin60 + tick_len * cn.sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                y = y_tick[1] - 2
                x = x_tick[1] + 1
                tick_label = Label(x=x, y=y, text_font_size=f"{tick_label_font_size}pt",
                                text=str(100-i*20), render_mode='css')
                self.plot.add_layout(tick_label)


        def draw_grids():        
            def draw_triangle_grids(offset: bool):
                delta = (100+gap) if offset else 0
                for i in range(1,5):
                    # left-right
                    x = [i*10+delta,100 - i*10 + delta]
                    y = [i*20 * cn.sin60, i*20 * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # horizontal
                    x = [i*20+delta,50 + i*10 + delta]
                    y = [0,(100 - i*20) * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # right-left
                    x = [i*20+delta,i*10 + delta]
                    y = [0, i*20 * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 

            def draw_diamond_grid():
                for i in range(1,5):   
                    # diamond left-right
                    x = [50 + gap/2 + i*10, 100 + gap/2 + i*10 ]
                    y = [(100 + gap + i * 20) * cn.sin60, (gap + i * 20) * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # diamond right-left
                    x = [100 + gap/2 + i*10, 50 + gap/2 + i*10 ]
                    y = [(200 + gap - i * 20) * cn.sin60, (100 + gap - i * 20) * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern)  
                    # diamond horizontal top
                    x = [50 + gap/2 + i*10, 100 + gap/2 + 50 - i*10 ]
                    y = [(100 + gap + i * 20) * cn.sin60, (100 + gap + i * 20) * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # diamond horizontal bottom
                    x = [100 + gap/2 + i*10, 100 + gap/2 - i*10]
                    y = [(gap + i * 20) * cn.sin60, (gap + i * 20) * cn.sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # middle line
                x = [50 + gap/2, 100 + gap + 50 -gap/2]
                y = [(100 + gap)*cn.sin60,(100 + gap)*cn.sin60]
                self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 

            
            def draw_axis_titles():
                def draw_ca_title():
                    x = 50 - 3
                    y = 0 - 3 - axis_title_font_size 
                    xa = [x - 2, x - 2 - arrow_size]
                    ya = [y + 2.5, y + arrow_size ]
                    title = 'Ca++'

                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{axis_title_font_size}pt",
                        text=title, text_font_style ='bold')
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=arrow_size), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                
                def draw_cl_title():
                    x = 100 + gap + 50 - 3
                    y = 0 - 3 - axis_title_font_size 
                    xa = [x + 7, x + 11]
                    ya = [y + 2.5, y + 2 ]
                    title = 'Cl-'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{axis_title_font_size}pt",
                        text=title, text_font_style ='bold')
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                
                def draw_mg_title():
                    x = 12
                    y = 44 - axis_title_font_size + 3
                    #self.plot.circle(x=x,y=y)
                    xa = [x + 9 * cn.cos60, x + 9 * cn.cos60 + 4 * cn.cos60]
                    ya = [y + 14 * cn.sin60, y + 14 * cn.sin60 + 4 * cn.sin60 ]

                    title = 'Mg++'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{axis_title_font_size}pt",
                        text=title, text_font_style ='bold',
                        angle = 60.5, # not sure why 60 gives the wrong angle
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_SO4_title():
                    x = 200 + gap - 25 - 13 * cn.cos60 + 14
                    y = 50 * cn.sin60 - axis_title_font_size + 15*cn.sin60
                    #self.plot.circle(x=x,y=y)
                    xa = [x + 2 * cn.cos60, x + 2 * cn.cos60 - 4 * cn.cos60]
                    ya = [y + 2 * cn.sin60, y + 2 * cn.sin60 + 4 * cn.sin60 ]

                    title = 'SO4--'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{axis_title_font_size}pt",
                        text=title, text_font_style ='bold',
                        angle = -60.5, # not sure why 60 gives the wrong angle
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_cl_so4_title():
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
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_ca_mg_title():
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
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_HCO3_CO3_title():
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
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_Na_K_title():
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
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)

                draw_ca_title()
                draw_cl_title()
                draw_mg_title()
                draw_SO4_title()
                draw_cl_so4_title()
                draw_ca_mg_title()
                draw_HCO3_CO3_title()
                draw_Na_K_title()

            def draw_main_labels(titles:list, offset:bool):
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
                self.plot.add_layout(tick_label)
                
                # Na+K/Cl: todo: find out how the calculate the length of the text
                if not offset:
                    x = 100 - 6 - len(titles[1]) + delta
                else:
                    x = 100 + delta
                y = 0 - axis_title_font_size * .8
                tick_label = Label(x=x, y=y,text_font_size=f"{axis_title_font_size}pt",
                    text=titles[1], text_font_style ='bold')
                self.plot.add_layout(tick_label)

                # Mg/SO4
                x = 50  + delta
                y = 100 * cn.sin60 + 2   
                tick_label = Label(x=x, y=y,text_font_size=f"{axis_title_font_size}pt",
                    text=titles[2], text_font_style ='bold')
                self.plot.add_layout(tick_label)

            draw_triangle_grids(offset=False)
            draw_triangle_grids(offset=True)
            draw_diamond_grid()
            draw_axis_titles()
            self.plot.legend.click_policy="mute"

        draw_xaxis_base(False)
        draw_xaxis_base(True)
        draw_triangle_left(False)
        draw_triangle_left(True)
        draw_triangle_right(False)
        draw_triangle_right(True)
        draw_diamond_ul()
        draw_diamond_ur()

        draw_grids()


    def draw_markers(self, df):
        i = 0
        station_col = cn.STATION_IDENTIFIER_COL
        items = list(df[station_col].dropna().unique())
        if len(items) > cn.MAX_LEGEND_ITEMS:
            warning = f'Plot has {len(items)} items, only the first {cn.MAX_LEGEND_ITEMS} will be shown. Use filters to further reduce the number of legend-items'
            helper.flash_text(warning, 'warning')
            items = items[:cn.MAX_LEGEND_ITEMS]
            
        for station in items:
            df_filtered = df[df[cn.STATION_IDENTIFIER_COL] == station]
            colors = ['red','green','blue','orange','yellow','red','green','blue','orange','yellow','red','green','blue','orange','yellow']
            markers = ['circle','rect','triangle','cross','circle','rect','triangle','cross''circle','rect','triangle','cross']
            #for index,row in df_filtered.iterrows():
            if markers[i]=='circle':
                self.plot.circle(df_filtered['x'], df_filtered['y'], legend_label=station, size=self.cfg['symbol_size'], color=colors[i], alpha=self.cfg['fill_alpha'])
            elif markers[i]=='rect':
                self.plot.square(df_filtered['x'], df_filtered['y'], legend_label=station,size=self.cfg['symbol_size'], color=colors[i], alpha=self.cfg['fill_alpha'])
            elif markers[i]=='triangle':
                self.plot.triangle(df_filtered['x'], df_filtered['y'], legend_label=station,size=self.cfg['symbol_size'], color=colors[i], alpha=self.cfg['fill_alpha'])
            elif markers[i]=='cross':
                self.plot.cross(df_filtered['x'], df_filtered['y'], legend_label=station,size=self.cfg['symbol_size'], color=colors[i], alpha=self.cfg['fill_alpha'])
            i+=1
            if i == len(markers):
                i=0
            self.plot.legend.location = legend_location


    def show_save_file_button(self):
        if st.button("Save png file"):
            filename = helper.get_random_filename('piper','png')
            export_png(p, filename=filename)
            helper.flash_text(f"The Piper plot has been saved to **{filename}** and is ready for download", 'info')
            with open(filename, "rb") as file:
                btn = st.download_button(
                    label="Download image",
                    data=file,
                    file_name=filename,
                    mime="image/png"
                )


    def get_plot(self):
        self.plot = figure(width=int(self.cfg['plot_width']), 
                           height=int(self.cfg['plot_width'] * cn.sin60), 
                           y_range=(-figure_padding_bottom, int((200+gap+figure_padding_top) * cn.sin60)), 
                           tools=[HoverTool()],
                           x_range=(-figure_padding_left, 200 + gap + figure_padding_right))
        
        #('Station', f"@{{{st.session_state.config.station_col}}}"),
        #("Ca", "@ca_pct")
        self.plot.add_tools(HoverTool(
                tooltips=[
                    ('Station', '@Probenahmestelle'),
                    ('Ca', '@ca_pct')
                ],
            )
        )
        self.draw_triangles()
        self.draw_axis()
        data_transformed = self.get_tranformed_data()
        self.draw_markers(data_transformed)
        
        return self.plot