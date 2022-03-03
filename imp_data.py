# streamlit app to import new data. db update works as follows:
# 1. streamlit run imp_data.py
# 2. press Run button: new stations are discovered and imported together with measurements
# 3. backup local database
# 4. restore remote database with the the option clean first: there are fail warnings but 
#    all objects are up-to-date

import streamlit as st
from io import StringIO
import pandas as pd
import numpy as np
import sqlalchemy as sql
from datetime import datetime
# import timeit

import database as db
import const as cn

conn = db.get_connection()


def load_columns(project:str):
    filename = f'./data/{project}_columns.csv'
    df = pd.read_csv(filename, sep=";")
    ok = db.save_db_table("temp_columns", df, [])
    st.info(ok)
    

def load_parameters(project):
    filename = f'./data/{project}_parameters.csv'
    df = pd.read_csv(filename, sep=";")
    ok = db.save_db_table("temp_parameters", df, [])
    st.info(ok)

def load_data(project):
    filename = f'./data/{project}_data.csv'
    df = pd.read_csv(filename, sep=";")
    ok = db.save_db_table("temp_data", df, [])
    st.info(ok)

def load_metadata():
    filename = f'./metadata/parameters_metadata.csv'
    df = pd.read_csv(filename, sep=";")
    ok = db.save_db_table("temp_parameters_metadata", df, [])
    st.info(ok)

def load_guidelines():
    filename = f'./guidelines/epa_mcl.csv'
    df = pd.read_csv(filename, sep="\t")
    st.write(df)
    ok = db.save_db_table("temp_epa_mcl", df, [])

    filename = f'./guidelines/epa_mclg.csv'
    df = pd.read_csv(filename, sep="\t")
    st.write(df)
    ok = db.save_db_table("temp_epa_mclg", df, [])
    st.info(ok)

project = st.sidebar.text_input("Project")
if st.sidebar.button("Load data"):
    #load_columns(project)
    #load_parameters(project)
    #load_data(project)
    #load_metadata()
    load_guidelines()

st.write(project)