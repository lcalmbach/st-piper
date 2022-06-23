import encodings
import streamlit as st
import pandas as pd
from pathlib import Path
from st_aggrid import AgGrid

import const as cn
from const import MP
from const import Codes, Date_types
from .metadata import Metadata
import helper
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .project import Project

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.language)
    
class FontusImport():
    def __init__(self, prj):
        self.project = prj
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}
        self.step = 0
        self.observation_df = pd.DataFrame()
        self.station_df = pd.DataFrame()

    def select_step(self):
        if lang == {}:
            set_lang()
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