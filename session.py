import streamlit as st
import pandas as pd

from query import qry
import database as db
from proj.user import User
from proj.project import Project
import const as cn
import database as db
from query import qry


def get_guideline_dict()->pd.DataFrame:
    sql = qry['guidelines']
    df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
    result = dict(zip(df['id'], df['title']))
    return result

def init():
    st.session_state.user = User(cn.DEFAULT_USER_ID)
    st.session_state.project = Project(cn.DEFAULT_PROJECT_ID)
    st.session_state.language = st.session_state.user.language
    st.session_state.project_dict, st.session_state.project_df = st.session_state.user.get_user_projects()
    st.session_state.guideline_dict = get_guideline_dict()
    st.session_state.enums = {}




