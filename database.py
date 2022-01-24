import streamlit as st
import psycopg2
import sqlalchemy as sql
import pandas as pd
import db_config as dbcn

mydb = ''

def save_db_table(table_name: str, df: pd.DataFrame, fields: list):
    ok = False
    engine = sql.create_engine('postgresql+psycopg2://postgres:password@localhost:5432/edex')
    conn = engine.raw_connection()
    conn.cursor().execute("SET search_path TO 'imp'")
    try:
        if len(fields) > 0:
            df = df[fields]
            st.write(df)
        df.to_sql(table_name, engine, if_exists='append', chunksize=20000, index=False)
        ok = True
        conn.commit
    except ValueError as vx:
        print(vx)
    except Exception as ex:
        print(ex)
    finally:
        return ok


def save_df2table(table_name: str, df: pd.DataFrame, fields: list):
    """
    Saves selected columns of a pandas dataframe to a database table
    """

    st.info(f'Appending rows from dataframe to table {table_name}')
    ok = save_db_table(table_name, df, fields)
    if ok:
        st.info(f'Dataframe was appended to table {table_name}')
    else:
        st.error(f'Dataframe could not be appended to table {table_name}')
    return df, ok


def execute_non_query(cmd: str, conn: object):
    ok = True
    err_msg = ''
    try:
        mycursor = conn.cursor()
        mycursor.execute(cmd)
        conn.commit()
    except Exception as ex:
        ok = False
        err_msg = ''# ex.message
    print(ok)
    return ok, err_msg

# @st.cache(suppress_st_warning=True)
def execute_query(query, conn):
    """Executes a query and returns a dataframe with the results"""
    ok=False
    err_msg=''
    try:
        ok = True
        result = pd.read_sql_query(query, conn)
    except Exception as ex:
        err_msg = ''#ex.message
        result = None
    return result, ok, err_msg


# @st.cache(suppress_st_warning=True)
def get_connection():
    """Reads the connection string and sets the sql_engine attribute."""

    conn = psycopg2.connect(
        host = dbcn.DB_HOST,
        database=dbcn.DB_DATABASE,
        user=dbcn.DB_USER,
        password=dbcn.DB_PASS)

    return conn

def get_value(query, conn):
    df, ok, err_msg = execute_query(query, conn)
    if len(df) > 0:
        result = df.iloc[0][df.columns[0]]
    else:
        ok=False
        result = None
    return result, ok, err_msg
