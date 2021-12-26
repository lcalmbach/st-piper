from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot
import itertools
from bokeh.palettes import Category10
from scipy.stats.stats import pearsonr

import helper
import const as cn

class Scatter:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.data = df
        self.cfg = cfg

    def add_correlation(self, p, df):
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

        df = df.dropna()
        df.columns = ['x','y']
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
        p.line(df['x'], df['y'], line_width=2, color='red')
        return p, corr_coeff

    def color_gen(self):
        yield from itertools.cycle(Category10[10])

    def get_plot(self):
        def init_plot():
            plot = figure(toolbar_location="above", 
                    tools = [],
                    plot_width = self.cfg['plot_width'], 
                    plot_height = self.cfg['plot_height'],
                    title = self.cfg['plot_title'])
            plot.title.align = "center"
            plot.yaxis.axis_label = f"{self.cfg['y_par']} (mg/L)"
            plot.xaxis.axis_label = f"{self.cfg['x_par']} (mg/L)"
            return plot

        plot = init_plot()
        color = self.color_gen()
        clr = next(color)
        df_stats = None
        # markers are grouped as legends
        if self.cfg['group_legend_by'] == None:
            m = plot.scatter(x=self.cfg['x_par'], y=self.cfg['y_par'], source=self.data, marker=cn.MARKERS[0], 
                size=self.cfg['symbol_size'], color=clr, alpha=self.cfg['fill_alpha'])
            plot.add_tools(HoverTool(
                tooltips=[
                    ('Station', f"@{st.session_state.config.station_col}"),
                    (self.cfg['x_par'], f"@{{{self.cfg['x_par']}}}"),
                    # todo: columns must be renamed, since spaces are not allowed here 
                    (self.cfg['y_par'], f"@{{{self.cfg['y_par']}}}")
                ],
                formatters={
                    '@date': 'datetime', # use 'datetime' formatter for 'date' field
                })
            )
        else:
            item_list = list(self.data[st.session_state.config.station_col].unique())
            legend_items = []
            for item in item_list:
                df = self.data[self.data[st.session_state.config.station_col] == item]
                clr = next(color)
                m =plot.scatter(x=self.cfg['x_par'], y=self.cfg['y_par'], source=df, marker=cn.MARKERS[0], 
                size = self.cfg['symbol_size'], color=clr, alpha=self.cfg['fill_alpha'])
                legend_items.append((item,[m]))

            legend = Legend(items=legend_items, 
                            location=(0, 0), click_policy="hide")
            plot.add_layout(legend, 'right')
        if self.cfg['show_corr_line']:
            plot, corr_coeff = self.add_correlation(plot, self.data[[self.cfg['x_par'], self.cfg['y_par']]])
            p_val = 0.05
            sign_result = 'Correlation is statisticically significant' if corr_coeff[3] < p_val else 'Correlation is not statisticically significant'
            df_stats = pd.DataFrame({'stat': ['Pearson correlation coefficient', 'associated two-tailed p-value',f'Intepretation (p = {p_val})','Y-axis intercept','slope'],
                               'value': [corr_coeff[2], corr_coeff[3], sign_result, corr_coeff[0], corr_coeff[1]]})

        return plot, df_stats
