from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span
from bokeh.transform import factor_mark, factor_cmap
from bokeh import palettes
import itertools
import helper
import const as cn


class Time_series:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.data = df
        self.cfg = cfg

    def add_markers(self, p, df):
        p.circle(x="x", y="y", size=self.cfg['symbol_size'], fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=df)
        return p

    def get_plot(self):
        p = figure(title=self.cfg['plot_title'], x_axis_type="datetime", 
                   toolbar_location="above", 
                   tools = [],
                   plot_width = self.cfg['width'], 
                   plot_height=self.cfg['height'])
        p.title.align = "center"
        p.yaxis.axis_label = 'Concentration (mg/L)'
        color = itertools.cycle(palettes.Category20_20) #helper.color_gen(self.cfg['palette'], 10)
        i=0
        legend_items = []
        for item in self.cfg['legend_items']:
            df = self.data[self.data[self.cfg['legend_col']] == item]
            df = df.rename(columns={f"{st.session_state.config.date_col}": 'date'})
            clr = next(color)
            l = p.line(x='date', y=st.session_state.config.value_col, line_color=clr, line_width = 2, alpha=self.cfg['fill_alpha'], source=df)
            m = p.scatter(x='date', y=st.session_state.config.value_col, source=df, marker=cn.MARKERS[i], 
                size=self.cfg['symbol_size'], color=clr, alpha=self.cfg['fill_alpha'])
            legend_items.append((item,[l,m]))
            i+=1
        if 'hlines' in self.cfg:
            for lin in self.cfg['hlines']:
                hline = Span(location=lin['location'], dimension='width', line_color=lin['color'], line_width=lin['width'])
                p.renderers.extend([hline])
        legend = Legend(items=legend_items, 
                        location=(0, 0), 
                        click_policy="hide")
        p.add_layout(legend, 'right')

        p.add_tools(HoverTool(
            tooltips=[
                ('Parameter', f'@{st.session_state.config.parameter_col}'),
                ('Date', '@date{%F}'),
                ('Value', '@Wert')
            ],
            formatters={
                '@date': 'datetime', # use 'datetime' formatter for 'date' field
            })
        )
        
        return p

