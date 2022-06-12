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
    def __init__(self, prj: List['Project']):
        self.project = prj
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}
        self.step = 0

    