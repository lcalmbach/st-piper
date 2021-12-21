from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
import xyzservices.providers as xyz
from pyproj import Proj # https://pyproj4.github.io/pyproj/stable/api/proj.html
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, LinearColorMapper
from matplotlib import colors
import helper
import const as cn

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

    def get_map_rectangle(self, df, rad: int, lat:str, lon:str):
        lat_avg, lon_avg = df[lat].mean(), df[lon].mean()
        x_avg, y_avg =  self.wgs84_to_web_mercator(lat_avg, lon_avg)
        x_min = x_avg - rad
        x_max = x_avg + rad
        y_min = y_avg - rad
        y_max = y_avg + rad
        return x_min, y_min, x_max, y_max

    def add_color_column(self, df):
        def get_color(row, par, max_val):
            color = colors.rgb2hex([row[self.cfg['parameter']] / max_val, 0, 0])
            return color

        cols = st.session_state.config.station_cols + [self.cfg['parameter']]
        df = df[cols]
        if self.cfg['aggregation'] == 'mean':
            df = df.groupby(st.session_state.config.station_cols).mean()
        elif self.cfg['aggregation'] == 'max':
            df = df.groupby(st.session_state.config.station_cols).max()
            
        elif self.cfg['aggregation'] == 'min':
            df = df.groupby(st.session_state.config.station_cols).min()
        df.reset_index(inplace=True)
        df = df.dropna()
        df['_color'] = 0
        max_val = df[self.cfg['parameter']].max()
        df['_color'] = df.apply(lambda row: get_color(row, self.cfg['parameter'], max_val), axis=1)
        return df

    def add_markers(self,p,df):
        def get_size(x):
            result = x / self.cfg['max_value'] * self.cfg['max_prop_size']
            if result > self.cfg['max_prop_size']:
                result = self.cfg['max_prop_size']
            elif result < self.cfg['min_prop_size']:
                result = self.cfg['min_prop_size']
            return result

        if 'parameter' in self.cfg:
            if self.cfg['prop_size_method'] == 'color':
                color_mapper = LinearColorMapper(palette=self.cfg['lin_palette'], 
                                                low=df[self.cfg['parameter']].min(), 
                                                high=df[self.cfg['parameter']].mean() * 2)
                p.scatter(x="x", y="y", 
                        size=self.cfg['symbol_size'], 
                        color={'field': self.cfg['parameter'], 'transform': color_mapper}, 
                        fill_alpha=self.cfg['fill_alpha'], source=df)
            else:
                # = df.apply(lambda x: get_size(x))
                df['_size'] = list(map(get_size, list(df[self.cfg['parameter']])))
                p.circle(x="x", y="y", size='_size', fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=df)
        else:
            p.circle(x="x", y="y", size=self.cfg['symbol_size'], fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=df)
        return p

    def get_plot(self):
        x = st.session_state.config.key2col()

        lat = x[st.session_state.config.latitude_col]
        lon = x[st.session_state.config.longitude_col]
        # if paramter is set, then create a color column
        if 'parameter' in self.cfg:
            df = self.add_color_column(self.data)
        else:
            df = self.data[st.session_state.config.sample_station_cols].drop_duplicates()

        df = df.rename(columns={st.session_state.config.station_col: 'station'})
        df = self.wgs84_to_web_mercator_df(df, lat, lon)
        tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
        x_min, y_min, x_max, y_max = self.get_map_rectangle(df, self.cfg['extent'], lat, lon)
        
        if 'parameter' in self.cfg:
            tooltips = f"""Station: @station,
                        {self.cfg['parameter']}: @{self.cfg['parameter']}"""
        else:
            tooltips = f"Station: @station"
        p = figure(x_range=(x_min,x_max),
                    y_range=(y_min,y_max),
                    x_axis_type="mercator",
                    y_axis_type="mercator",
                    width = 800,
                    tooltips=tooltips)
        p.add_tile(tile_provider)
        p = self.add_markers(p, df)
        
        return p

