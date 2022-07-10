import encodings
import streamlit as st
import pandas as pd
from pathlib import Path
from st_aggrid import AgGrid

import const as cn
from const import MP, Codes, Date_types
from .metadata import Metadata
import helper
import proj.database as db
from typing import List, TYPE_CHECKING
from query import qry

if TYPE_CHECKING:
    from .project import Project

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)
    
class FontusImport():
    def __init__(self, prj):
        self.project = prj
        self.station_columns = {}
        self.sample_columns = {}
        self.columns_df = self.read_columns()
        self.step = 0
        self.observation_df = pd.DataFrame()
        self.station_df = pd.DataFrame()
        set_lang()

    def read_columns(self):
        sql = qry['project_columns'].format(self.project.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def get_column_df(self, column_types:list):
        df = self.columns_df
        df = df.query('type_id.isin(@column_types)')
        return df

    def get_column_list(self, column_type:int):
        df = self.columns_df
        df = df.query('type_id == @column_type')
        return list(df['source_column_name'])

    def get_column_name(self,master_par_id:int):
        df = self.columns_df
        df = df.query('master_parameter_id == @master_par_id')
        return df.iloc[0]['source_column_name']

    def select_step(self):
        steps = lang['steps']
        st.sidebar.markdown(f"**Step {self.step}:**")
        st.sidebar.markdown(steps[self.step])
        
        cols = st.sidebar.columns([4,8])
        with cols[0]:
            if st.button('Previous', disabled=(self.step == 0)):
                self.step -=1
        with cols[1]:
            if st.button('Next', disabled=False): # not(self.step_success)
                self.step +=1
        self.run_step()