import streamlit as st
from bokeh.io import export_png, export_svgs
import time
import pandas as pd
import numpy as np
from datetime import datetime
import const as cn
from bokeh import palettes
import itertools
import base64
import json
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pycountry
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode,GridUpdateMode


def flash_text(text:str, type:str):
    placeholder = st.empty()
    if type=='info':
        placeholder.info(text)
    elif type=='success':
        placeholder.success(text)
    else:
        placeholder.warning(text)
    time.sleep(5)
    placeholder.write("")


def get_random_filename(prefix: str, ext: str):
    # todo: add further folders
    folder = 'images'
    suffix = datetime.now().strftime("%y%m%d_%H%M%S")
    return f"./{folder}/{prefix}-{suffix}.{ext}"

def isnan(text):
    return text != text


def add_pct_columns(df:pd.DataFrame, par_dict:dict, pmd)->pd.DataFrame:
    """
    converts mg/L concentrations to meq/L, meq% to be used in the piper diagram
    and the ion balance.

    Args:
        df (pd.DataFrame):  dataframe in the sample per row format with all major ions columns
        par_dict(dict):     dict holding formula weights

    Returns:
        pd.DataFrame: same dataframe with added columns xx_meqpl, xx_meqpct for each major ion
    """
    df = calc_meql(df, par_dict, pmd)
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


def calc_meql(df: pd.DataFrame, pars: dict, pmd: pd.DataFrame):
    """
    Adds a new column xx_mqpl for all major ions xx
    """
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

def date_filter(df, cols):
    date_col = st.session_state.config.key2col()[cn.SAMPLE_DATE_COL]
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    with cols[0]:
        date_from = st.date_input("Date from", min_date)
    with cols[1]:
        date_to = st.date_input("Date to", max_date)
    is_filtered = (date_from != min_date) | (date_to != max_date)
    return date_from, date_to, is_filtered

def show_save_file_button(p, key: str):
    if st.button("Save png file", key=key):
        filename = get_random_filename('piper','png')
        export_png(p, filename=filename)
        flash_text(f"The plot has been saved to **{filename}** and is ready for download", 'info')
        with open(filename, "rb") as file:
            btn = st.download_button(
                label="Download image",
                data=file,
                file_name=filename,
                mime="image/png"
            )

def transpose_row(df):
    result = pd.DataFrame()
    for fld in df.columns:
        result = result.append({'parameter': fld, 'value': df.iloc[0][fld]}, ignore_index=True)
    return result

def nd2numeric(df):
    col_name = df.columns[0]
    nd_flag_col = 'nd_flag'
    num_val_col = 'num_val_col'
    df[nd_flag_col] = False
    df[col_name] = df[col_name].astype(str)
    df.loc[df[col_name].str.startswith('<') == True, nd_flag_col] = True
    df.loc[df[nd_flag_col] == True, num_val_col] = df[col_name].str.replace('<', '')
    df.loc[(df[nd_flag_col] == False), num_val_col] = pd.to_numeric(df[col_name],errors='coerce') 
    df[num_val_col] = df[num_val_col].astype('float') 
    df.loc[(df[nd_flag_col] == True) & (df[num_val_col] != 0), num_val_col] = df[num_val_col] / 2
    df = df[num_val_col]
    df.columns = col_name
    return df

def select_parameter(sidebar_flag: bool):
    parameter_options = list(st.session_state.config.parameter_map_df.index)
    parameter_options.sort()
    if sidebar_flag:
        sel_parameter = st.sidebar.selectbox('Parameter', parameter_options)
    else:
        sel_parameter = st.selectbox('Parameter', parameter_options)
    return sel_parameter

def bokeh_palettes(n: int)->list:
    """
    Returns a list of available bokeh palettes for a given number of required colors

    Args:
        n (int): required colors

    Returns:
        list: available palettes for specified number of required colors
    """

    colors = palettes.__palettes__
    return list(filter(lambda col: col.find(str(n)) > 0, colors))

def color_gen(palette, n):
    yield from itertools.cycle(palettes[palette])

def aggregate_data(source: pd.DataFrame, group_cols: list, val_col: str, agg_func: str):
    df = source[group_cols + [val_col]]
    if agg_func == 'mean':
        df = df.groupby(group_cols).mean()
    elif agg_func == 'max':
        df = df.groupby(group_cols).max()
    elif agg_func == 'min':
        df = df.groupby(group_cols).min()
    df.reset_index(inplace=True)
    df = df.dropna()
    return df

def get_base64_encoded_image(image_path):
    """
    returns bytecode for an image file
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def get_language(py_file: str, lang:str):
    """ 
    extract the language dict from a json file located in ./locales folder
    """

    lang_file = f"./locales/{py_file}.json"
    with open(lang_file, 'r', encoding='utf8') as myfile:
        data=myfile.read()
    lang_df = pd.DataFrame(json.loads(data)).reset_index()
    land_df = lang_df[lang_df['index']==lang]
    lang_dict = land_df.iloc[0].to_dict()
    return lang_dict

def merge_sentences(sentences: list):
    text = ''
    for item in sentences:
        text+=item
    return text

def get_distinct_values(df: pd.DataFrame, field:str):
    result = df[field].unique()


class Mail:
    def __init__(self):
        self.port = 465
        self.smtp_server_domain_name = "smtp.gmail.com"
        self.sender_mail = "lcalmbach@gmail.com"
        self.password = "d@d63 rocks!"

    def send(self, emails, subject, content):
        ssl_context = ssl.create_default_context()
        service =  smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)
        msg = MIMEMultipart('html')
        msg['Subject'] = subject
        msg['From'] = self.sender_mail
        msg['To'] = emails[0]
        html = MIMEText(content, 'html')
        msg.attach(html)
        result = service.sendmail(from_addr=self.sender_mail, to_addrs=emails, msg=msg.as_string())
        service.quit()
        return result
    
def get_country_list():
    result = {}
    for country in pycountry.countries:
        result[country.alpha_3] = country.name
    return result

def show_table(df: pd.DataFrame, cols, settings):
    gb = GridOptionsBuilder.from_dataframe(df)
    #customize gridOptions
    if 'update_mode' not in settings:
        settings['update_mode']=GridUpdateMode.SELECTION_CHANGED
    gb.configure_default_column(groupable=False, value=True, enableRowGroup=False, aggFunc='sum', editable=False)
    for col in cols:
        gb.configure_column(col['name'], type=col['type'], precision=col['precision'], hide=col['hide'])
    gb.configure_selection(settings['selection_mode'], use_checkbox=False)#, rowMultiSelectWithClick=rowMultiSelectWithClick, suppressRowDeselection=suppressRowDeselection)
    gb.configure_grid_options(domLayout='normal')
    gridOptions = gb.build()

    grid_response = AgGrid(
        df, 
        gridOptions=gridOptions,
        height=settings['height'], 
        data_return_mode=DataReturnMode.AS_INPUT, 
        update_mode=settings['update_mode'],
        fit_columns_on_grid_load=settings['fit_columns_on_grid_load'],
        allow_unsafe_jscode=True, 
        enable_enterprise_modules=True,
        )
    selected = grid_response['selected_rows']
    selected_df = pd.DataFrame(selected)
    return selected_df

def select_project_from_grid():
    df = st.session_state.config.projects_df[['id', 'title']]
    settings = {}
    settings['height'] = 200
    settings['width'] = "400px"
    settings['selection_mode']='single'
    settings['fit_columns_on_grid_load'] = True
    settings['update_mode']=GridUpdateMode.SELECTION_CHANGED
    cols = []
    cols.append({'name': 'id', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0, 'hide':True})
    sel_row = show_table(df,cols,settings)
    if len(sel_row)>0:
        return int(sel_row.iloc[0]['id'])
    else:
        return -1

def get_filter(filters):
    expression = ''
    with st.sidebar.expander('🔎 Filter'):
        if 'stations' in filters:
            station_dict=st.session_state.config.project.get_station_list(allow_none=False)
            stations = st.multiselect(label="Stations", options=list(station_dict.keys()),
                                        format_func=lambda x:station_dict[x])
            if len(stations)>0:
                stations = ",".join(map(str, stations))
                expression = f"station_id in ({stations})"
        if 'sampling_date' in filters:
            min_date, max_date = st.session_state.config.project.min_max_date()
            minmax = st.date_input("Date", min_value=min_date, max_value=max_date,value = (min_date,max_date))
            if minmax !=  (min_date,max_date):
                expression = "{expression} AND " if expression > '' else ""
                expression += f"sampling_date >= '{minmax(0)}' and sampling_date <= '{minmax(1)}'"
    
    return expression

def get_stations(default: list, filter:str):
    station_dict=st.session_state.config.project.get_station_list(allow_none=False)
    stations = st.sidebar.multiselect(label="Stations", options=list(station_dict.keys()),
                                        format_func=lambda x:station_dict[x],
                                        default = default)
    return stations

def get_parameters(default: list, filter: str):
    parameter_dict = st.session_state.config.project.get_parameter_dict(allow_none=False, filter="")
    sel_parameters = st.sidebar.multiselect(label='Parameter', options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x], 
                                            default=default)
    return sel_parameters

def get_parameter(default: int, filter: str = '', label: str = 'Parameter'):
    parameter_dict = st.session_state.config.project.get_parameter_dict(allow_none=False, filter=filter)
    id = list(parameter_dict.keys()).index(default)
    sel_parameter = st.sidebar.selectbox(label=label, options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x], 
                                            index=id)
    return sel_parameter

def get_guideline(default: list):
    guideline_dict = st.session_state.config.get_guideline_dict()
    default_id = list(guideline_dict.keys()).index(default)
    sel_guideline = st.sidebar.selectbox(label='Guideline', options=list(guideline_dict.keys()), 
                                            format_func=lambda x:guideline_dict[x], 
                                            index=default_id)
    return sel_guideline

def add_meqpl_columns(data, parameters, columns):
    st.write(parameters)
    for par_id in parameters:
        id = parameters.index(par_id)
        col = columns[id]
        fact = st.session_state.config.lookup_parameters.unit_conversion(par_id, None, 'meq/L')