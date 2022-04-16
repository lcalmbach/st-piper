import pandas as pd
import numpy as np
import streamlit as st
from bokeh.models.tools import SaveTool
from bokeh.plotting import figure
# from bokeh.models import Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot, SingleIntervalTicker, FuncTickFormatter

import helper
import const as cn

class Boxplot:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.cfg = cfg
        self.data = df

    def get_plot(self):
        # Find the quartiles and IQR foor each category
    
        df = self.data
        groups = df.groupby('group')
        q1 = groups.quantile(q=0.25)
        q2 = groups.quantile(q=0.5)
        q3 = groups.quantile(q=0.75)
        iqr = q3 - q1
        upper = q3 + 1.5*iqr
        lower = q1 - 1.5*iqr

        # find the outliers for each category
        def outliers(group):
            cat = group.name
            return group[(group.score > upper.loc[cat][0]) | (group.score < lower.loc[cat][0])]['score']
        out = groups.apply(outliers).dropna()

        # Prepare outlier data for plotting, we need coordinate for every outlier.
        outx = []
        outy = []
        cats = df['group'].unique()
        for cat in cats:
            # only add outliers if they exist
            if not out.loc[cat].empty:
                for value in out[cat]:
                    outx.append(cat)
                    outy.append(value)

        p = figure(tools="save", background_fill_color=self.cfg['background_fill_color'], title="", x_range=cats)

        # If no outliers, shrink lengths of stems to be no longer than the minimums or maximums
        qmin = groups.quantile(q=0.00)
        qmax = groups.quantile(q=1.00)
        upper.score = [min([x,y]) for (x,y) in zip(list(qmax.iloc[:,0]),upper.score) ]
        lower.score = [max([x,y]) for (x,y) in zip(list(qmin.iloc[:,0]),lower.score) ]

        # stems
        p.segment(cats, upper.score, cats, q3.score, line_width=2, line_color="black")
        p.segment(cats, lower.score, cats, q1.score, line_width=2, line_color="black")

        # boxes
        p.rect(cats, (q3.score+q2.score)/2, 0.7, q3.score-q2.score,
            fill_color=self.cfg['upper_box_fill_color'], fill_alpha=self.cfg['box_alpha'], line_width=2, line_color="black")
        p.rect(cats, (q2.score+q1.score)/2, 0.7, q2.score-q1.score,
            fill_color=self.cfg['lower_box_fill_color'], fill_alpha=self.cfg['box_alpha'], line_width=2, line_color="black")

        # whiskers (almost-0 height rects simpler than segments)
        p.rect(cats, lower.score, 0.2, 0.01, line_color="black")
        p.rect(cats, upper.score, 0.2, 0.01, line_color="black")

        # outliers
        p.circle(outx, outy, size=6, color="#F38630", fill_alpha=self.cfg['symbol_alpha'])

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = self.cfg['grid_line_color']
        p.grid.grid_line_width = self.cfg['grid_line_width']
        p.grid.grid_line_dash = self.cfg['grid_line_dash']
        
        p.xaxis.major_label_text_font_size = self.cfg['x_axis_major_label_text_font_size']
        
        p.yaxis.axis_label = self.cfg['y_axis_title']
        p.yaxis.major_label_text_font_size = self.cfg['y_axis_major_label_text_font_size']
        p.yaxis.axis_label_text_font_size = self.cfg['axis_label_text_font_size']
        return p
