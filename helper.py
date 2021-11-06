import streamlit as st
import time
import pandas as pd
from datetime import datetime
import const as cn

def flash_text(text:str,type:str):
    placeholder = st.empty()
    placeholder.info(text)
    time.sleep(5)
    placeholder.write("")


def get_random_filename(prefix: str, ext: str):
    # todo: add further folders
    folder = 'images'
    suffix = datetime.now().strftime("%y%m%d_%H%M%S")
    return f"./{folder}/{prefix}-{suffix}.{ext}"
    

def get_parameter_columns(column_type: str):
    df = pd.DataFrame(cn.PARAMETERS).query('type=@column_type')
    return list