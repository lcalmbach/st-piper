from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
import xyzservices.providers as xyz
# from pyproj import Proj # https://pyproj4.github.io/pyproj/stable/api/proj.html
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, LinearColorMapper
import helper
import const as cn
from matplotlib import colors

class Map:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.data = df
        self.cfg = cfg

    def wgs84_to_web_mercator_df(self, df, lat, lon):
        k = 6378137
        df["x"] = df[lon] * (k * np.pi/180.0)
        df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

        return df

    def wgs84_to_web_mercator(self, lat, lon):
        k = 6378137
        x = lon * (k * np.pi/180.0)
        y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
        return x, y

    def get_map_rectangle(self, df):
        x_min = df['x'].min()
        x_max = df['x'].max()
        y_min = df['y'].min()
        y_max = df['y'].max()
        return x_min, y_min, x_max, y_max

    def get_prop_size(self, df):
        def get_size(x):
            result = x / self.cfg['max_value'] * self.cfg['max_prop_size']
            if result > self.cfg['max_prop_size']:
                result = self.cfg['max_prop_size']
            elif result < self.cfg['min_prop_size']:
                result = self.cfg['min_prop_size']
            return result

        df[cn.PROP_SIZE_COL] = 0
        df[cn.PROP_SIZE_COL] = list(map(get_size, list(df[st.session_state.config.value_col])))
        return df

    def add_markers(self, p, df):
        if 'parameter' in self.cfg:
            if self.cfg['prop_size_method'] == 'color':
                color_mapper = LinearColorMapper(palette=self.cfg['lin_palette'], 
                                                low=0, 
                                                high=self.cfg['max_value'])
                p.scatter(x="x", y="y", 
                        size=self.cfg['symbol_size'], 
                        color={'field': st.session_state.config.value_col, 'transform': color_mapper}, 
                        fill_alpha=self.cfg['fill_alpha'], source=self.data)
            else:
                df = self.get_prop_size(df)
                p.circle(x="x", y="y", size=cn.PROP_SIZE_COL, fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=self.data)
        else:
            p.circle(x="x", y="y", size=self.cfg['symbol_size'], fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=self.data)
        return p

    def get_plot(self):
        # if paramter is set, then create a color column
        if 'parameter' in self.cfg:
            df = helper.aggregate_data(source=self.data,
                                       group_cols=st.session_state.config.station_cols, 
                                       val_col=st.session_state.config.value_col, 
                                       agg_func=self.cfg['aggregation'])
            tooltips = f"""Station: @identifier<br>
                        {self.cfg['parameter']}: @{{{st.session_state.config.value_col}}}{{0.00}}"""
        else:
            pass
            tooltips = f"Station: @identifier"
            
        #df = df.rename(columns={st.session_state.config.station_col: 'station'})
        self.data = self.wgs84_to_web_mercator_df(self.data, self.cfg['long'], self.cfg['lat'])
        tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
        x_min, y_min, x_max, y_max = self.get_map_rectangle(self.data)
        
        p = figure(x_range=(x_min,x_max),
                   y_range=(y_min,y_max),
                   x_axis_type="mercator",
                   y_axis_type="mercator",
                   width = self.cfg['plot_width'],
                   tooltips=tooltips)
        p.add_tile(tile_provider)
        p = self.add_markers(p, self.data)
        
        return p

