import streamlit as st
import time
import pandas as pd
import numpy as np
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
    

def isnan(text):
    return text != text

def complete_columns(df:pd.DataFrame, par_dict:dict)->pd.DataFrame:
    """converts mg/L concentrations to meq/L, meq% to be used in the piper diagram
    and the ion balance.

    Args:
        df (pd.DataFrame): dataframe in the sample per row format with all major ions columns

    Returns:
        pd.DataFrame: same dataframe with added columns xx_meqpl, xx_meqpct for each major ion
    """
    df = calc_meql(df, par_dict)
    df = calc_pct(df)
    df = calculate_electroneutrality(df)
    return df

def major_ions_complete(df:pd.DataFrame)->bool:
    """return wether there are columns for all major ions:
    Na, Ca, Mg, Alk, Cl, SO4. K is optionional but is used when present.

    Args:
        df (pd.DataFrame): [description]

    Returns:
        bool: [description]
    """
    ok=[False]*6
    ok[0] = 'ca_pct' in df.columns
    ok[1] = 'mg_pct' in df.columns
    ok[2] = 'na_pct' in df.columns
    ok[3] = 'cl_pct' in df.columns
    ok[4] = ('alk_pct' in df.columns) or ('hco3_pct' in df.columns)
    ok[5] = 'so4_pct' in df.columns
    return all(ok)


def calc_pct(df: pd.DataFrame):
    """
    Converts major ions from meq/L to meq%. The following ions are used. CA, Mg, Na
    K (if available),

    Args:
        df (pd.DataFrame): [description]

    Returns:
        [type]: [description]
    """

    if 'na_k_meqpl' in df.columns:
        df['sum_cations'] = df['ca_meqpl'] + df['na_k_meqpl'] + df['mg_meqpl']
    else:
        df['sum_cations'] = df['ca_meqpl'] + df['na_meqpl'] + df['mg_meqpl']
    df['ca_pct'] = df['ca_meqpl'] / df['sum_cations'] * 100
    df['na_pct'] = df['na_meqpl'] / df['sum_cations'] * 100
    if 'k_pct' in df.columns:
        df['k_pct'] = df['k_meqpl'] / df['sum_cations'] * 100
        df['na_k_pct'] = df['na_k_meqpl'] / df['sum_cations'] * 100
    df['mg_pct'] = df['mg_meqpl'] / df['sum_cations'] * 100

    df['sum_anions'] = df['alk_meqpl'] + df['cl_meqpl'] + df['so4_meqpl']
    df['alk_pct'] = df['alk_meqpl'] / df['sum_anions'] * 100
    df['cl_pct'] = df['cl_meqpl'] / df['sum_anions'] * 100
    df['so4_pct'] = df['so4_meqpl'] / df['sum_anions'] * 100
    return df

def calculate_electroneutrality(df: pd.DataFrame):
    df['ion_balance_pct'] = (df['sum_cations'] - df['sum_anions']) / (df['sum_cations'] + df['sum_anions']) * 100
    return df


def calc_meql(df: pd.DataFrame, pars: dict):
    """
    Adds a new column xx_mqpl for all major ions xx
    """

    pmd = st.session_state.config.lookup_parameters.metadata_df
    if 'ca' in pars.keys():
        df['ca_meqpl'] = df[pars['ca']] / pmd.loc['ca']['fmw'] * abs(pmd.loc['ca']['valence'])

    if 'na' in pars.keys():
        df['na_meqpl'] = df[pars['na']] / pmd.loc['na']['fmw'] * abs(pmd.loc['na']['valence'])
    if 'k' in pars.keys():
        df['k_meqpl'] = df[pars['k']] / pmd.loc['k']['fmw'] * abs(pmd.loc['k']['valence'])
    if 'mg' in pars.keys():    
        df['mg_meqpl'] = df[pars['mg']] / pmd.loc['mg']['fmw'] * abs(pmd.loc['mg']['valence'])
    if 'alk' in pars.keys():   
        #df['alk_meqpl'] = df[pars['alk']] / pmd.loc['alk']['fmw'] * abs(pmd.loc['alk']['valence'])
        df['alk_meqpl'] = df[pars['alk']]  * abs(pmd.loc['alk']['valence'])
    if 'cl' in pars.keys():    
        df['cl_meqpl'] = df[pars['cl']] / pmd.loc['cl']['fmw'] * abs(pmd.loc['cl']['valence'])
    if 'so4' in pars.keys():    
        df['so4_meqpl'] = df[pars['so4']] / pmd.loc['so4']['fmw'] * abs(pmd.loc['so4']['valence'])
    if ('na' in pars.keys()) and ('k' in pars.keys()):   
        df['na_k_meqpl'] = df['na_meqpl']  + df['k_meqpl'] 
    return df

def add_not_used2dict(dic:dict)->dict:
    """Adds a not used entry at the top of the dict

    Args:
        dic (dict): dict where 'not used' item is inserted at the top

    Returns:
        dict: dict with the inserted new item 'not used'
    """

    result = dict({cn.NOT_USED:cn.NOT_USED})
    result.update(dic)
    return result

def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = 'percentile_%s' % n
    return percentile_
