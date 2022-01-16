import pandas as pd
import numpy as np
import streamlit as st
from bokeh.models.tools import SaveTool
from bokeh.plotting import figure
from bokeh.models import Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot, SingleIntervalTicker, FuncTickFormatter
import itertools
from bokeh.palettes import Category10

import helper
import const as cn

class Boxplot:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.identifier_col = 'Probennummer'
        self.cfg = cfg
        self.data = df
        
    def color_gen(self):
        yield from itertools.cycle(Category10[10])


    def get_plot(self):
        df = self.data
        cats = self.cfg['box_group_values']
        # find the quartiles and IQR for each category
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
            return group[(group.score > upper.loc[cat]['score']) | (group.score < lower.loc[cat]['score'])]['score']
        out = groups.apply(outliers).dropna()

        # prepare outlier data for plotting, we need coordinates for every outlier.
        if not out.empty:
            outx = list(out.index.get_level_values(0))
            outy = list(out.values)

        p = figure(tools="", background_fill_color="white", x_range=cats, toolbar_location=None)

        # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
        qmin = groups.quantile(q=0.00)
        qmax = groups.quantile(q=1.00)
        upper.score = [min([x,y]) for (x,y) in zip(list(qmax.loc[:,'score']),upper.score)]
        lower.score = [max([x,y]) for (x,y) in zip(list(qmin.loc[:,'score']),lower.score)]

        # stems
        p.segment(cats, upper.score, cats, q3.score, line_color="black")
        p.segment(cats, lower.score, cats, q1.score, line_color="black")

        # boxes
        p.vbar(cats, 0.7, q2.score, q3.score, fill_color="blue", line_color="black")
        p.vbar(cats, 0.7, q1.score, q2.score, fill_color="blue",  fill_alpha=0.6, line_color="black")

        # whiskers (almost-0 height rects simpler than segments)
        p.rect(cats, lower.score, 0.2, 0.01, line_color="black")
        p.rect(cats, upper.score, 0.2, 0.01, line_color="black")

        # outliers
        if not out.empty:
            p.circle(outx, outy, size=6, color="orange", fill_alpha=0.6)

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = "lightgrey"
        p.ygrid.grid_line_dash = "dashed"
        p.grid.grid_line_width = 1
        p.xaxis.major_label_text_font_size="16px"

        return p
