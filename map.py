from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
import xyzservices.providers as xyz
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, GMapOptions
from bokeh.plotting import gmap
from streamlit.delta_generator import MAX_DELTA_BYTES
from datetime import datetime, timedelta

import helper
import const as cn



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

def wgs84_to_web_mercator_df(df, lon=cn.LONGITUDE_COL, lat=cn.LATITUDE_COL):
      k = 6378137
      df["x"] = df[lon] * (k * np.pi/180.0)
      df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

      return df

def show_map(data):
    def wgs84_to_web_mercator(lat, lon):
        k = 6378137
        x = lon * (k * np.pi/180.0)
        y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
        return x, y

    def get_map_rectangle(df, rad: int):
        lat_avg, lon_avg = df[lat].mean(), df[lon].mean()
        x_avg, y_avg = wgs84_to_web_mercator(lat_avg, lon_avg)
        x_min = x_avg - rad
        x_max = x_avg + rad
        y_min = y_avg - rad
        y_max = y_avg + rad
        return x_min, y_min, x_max, y_max

    x = st.session_state.config.key2col()

    lat = x[cn.LATITUDE_COL]
    lon = x[cn.LONGITUDE_COL]
    station = x[cn.STATION_IDENTIFIER_COL]
    df = data[[lat, lon, station]].drop_duplicates()
    df = df.rename(columns={st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]: 'station'})
    df = wgs84_to_web_mercator_df(df)
    tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
    x_min, y_min, x_max, y_max = get_map_rectangle(df, 7000)
    #map_options = GMapOptions(lat=47.55, lng=7.58, map_type="roadmap", zoom=11)
    # p = gmap("GOOGLE_API_KEY", map_options, title="Austin")
    
    p = figure(x_range=(x_min,x_max),
                y_range=(y_min,y_max),
                x_axis_type="mercator",
                y_axis_type="mercator",
                width = 800,
                tooltips=f"Station: @station")
    p.add_tile(tile_provider)

    #source = ColumnDataSource(
    #    data=dict(lat=list(df['x']),
    #              lon=list(df['y']))
    #     )
    p.circle(x="x", y="y", size=10, fill_color="darkblue", fill_alpha=0.8, source=df)
    st.bokeh_chart(p)
    
    show_save_file_button(p)

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
        show_map(data)
    

