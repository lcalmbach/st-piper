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
import os
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode,GridUpdateMode
from query import qry
import database as db

from deprecated import deprecated

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
    date_col = st.session_state.key2col()[cn.SAMPLE_DATE_COL]
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

def select_parameter_obsolet(sidebar_flag: bool):
    parameter_options = list(st.session_state.parameter_map_df.index)
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
    st.write(source)
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

def get_lang(lang:str, py_file: str) -> dict:
    """
    extract the language dict from a json file located in ./locales folder of the package folder
    every module requireing language support requests a locales subfolder in its package folder
    """

    path = os.path.dirname(py_file)
    path=os.path.join(path, 'locales')
    file_name_no_ext = os.path.splitext(os.path.basename(py_file))[0]
    lang_file = os.path.join(path, file_name_no_ext + '.json')
    # st.write(lang_file)
    with open(lang_file, 'r', encoding='utf8') as myfile:
        data=myfile.read()
    lang_df = pd.DataFrame(json.loads(data)).reset_index()
    land_df = lang_df[lang_df['index']==lang]
    lang_dict = land_df.iloc[0].to_dict()
    return lang_dict

@deprecated
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
        self.password = "pink rhin0!"

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


def get_filter(filters):
    expression = ''
    with st.sidebar.expander('🔎 Filter'):
        if 'stations' in filters:
            station_dict=st.session_state.project.get_station_list(allow_none=False)
            stations = st.multiselect(label="Stations", options=list(station_dict.keys()),
                                        format_func=lambda x:station_dict[x])
            if len(stations)>0:
                stations = ",".join(map(str, stations))
                expression = f"station_id in ({stations})"
        if 'sampling_date' in filters:
            min_date, max_date = st.session_state.project.min_max_date()
            minmax = st.date_input("Date", min_value=min_date, max_value=max_date,value = (min_date,max_date))
            if minmax !=  (min_date, max_date):
                expression = f"{expression} AND " if expression > '' else ""
                expression += f"sampling_date >= '{minmax[0]}' and sampling_date <= '{minmax[1]}'"
    
    return expression

def get_station(default: int, filter:str):
    station_dict=st.session_state.project.get_station_list(allow_none=False)
    if default in list(station_dict.values()):
        id = list(station_dict.values()).index(default)
    else:
        id = 0
    station_id = st.sidebar.selectbox(label="Station", options=list(station_dict.keys()),
                                        format_func=lambda x:station_dict[x],
                                        index=id)
    return station_id

def get_date(station_id: int, default):
    date_dict=st.session_state.project.get_date_list(station_id=station_id,allow_none=False, )
    if default in list(date_dict.values()):
        id = list(date_dict.values()).index(default)
    else:
        id = 0
    sampling_date = st.sidebar.selectbox(label="Sampling date", options=list(date_dict.keys()),
                                        format_func=lambda x:date_dict[x],
                                        index=id)
    return sampling_date


def get_stations(default: list, filter:str):
    station_dict=st.session_state.project.get_station_list(allow_none=False)
    stations = st.sidebar.multiselect(label="Stations", options=list(station_dict.keys()),
                                        format_func=lambda x:station_dict[x],
                                        default = default)
    return stations

def get_parameters(default: list, filter: str):
    parameter_dict = st.session_state.project.get_parameter_dict(allow_none=False, filter="")
    sel_parameters = st.sidebar.multiselect(label='Parameter', options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x], 
                                            default=default)
    return sel_parameters

def get_parameter(default: int, filter: str = '', label: str = 'Parameter'):
    parameter_dict = st.session_state.project.get_parameter_dict(allow_none=False, filter=filter)
    id = list(parameter_dict.keys()).index(default)
    sel_parameter = st.sidebar.selectbox(label=label, options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x], 
                                            index=id)
    return sel_parameter

def get_guideline(default: list):
    default_id = list(st.session_state.guideline_dict.keys()).index(default)
    sel_guideline = st.sidebar.selectbox(label='Guideline', options=list(st.session_state.guideline_dict.keys()), 
                                            format_func=lambda x:st.session_state.guideline_dict[x], 
                                            index=default_id)
    return sel_guideline

def add_meqpl_columns(data, parameters, columns):
    for par_id in parameters:
        id = parameters.index(par_id)
        col = columns[id]
        fact = st.session_state.project.unit_conversion(par_id, None, 'meq/L')
        data[col] = data[par_id] * fact

    return data

def add_pct_columns(data:pd.DataFrame, parameters:list, new_columns:list, sum_col: str):
    """
    converts columns into percent, e.g. meq > meq%. 
    
    Args:
        data (pd.DataFrame): dataframe holding columns to be converted
        parameters (list): list of parameter ids
        columns (list): list of new column names
        sum_col(str):   name of sum column
    Returns:
        _type_: _description_
    """

    data[sum_col] = data[parameters].sum(axis=1)
    for par in parameters:
        id = parameters.index(par)
        new_col = new_columns[id]
        data[new_col] = np.where(data[sum_col]==0, 0, data[par] / data[sum_col] * 100)

    return data

def get_lookup_code_dict(category: int, lang: str)->dict:
    """returns a dictionary for the lookup_codes table

    Args:
        category (int): see const.Codes enum
        lang (str): languange (en, de, zh)

    Returns:
        dict: id, name key-values
    """
    sql = qry['lookup_values'].format(lang, category.value)
    df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
    result = dict(zip(df['id'], df['name']))
    return result

def load_data_from_file(uploaded_file: st.uploaded_file_manager.UploadedFile, preview: bool)->pd.DataFrame:
    """
    reads a csv file and returns the data in a dataframe

    Args:
        uploaded_file (st.uploaded_file_manager.UploadedFile): uploaded file
        preview (bool): check if you want to see a preview of the file (todo: remove)

    Returns:
        pd.DataFrame: content of csv file
    """
    df = pd.read_csv(uploaded_file, 
        sep=st.session_state.project.separator, 
        encoding=st.session_state.project.encoding)
    flash_text(f"File was loaded: {len(df)} rows, {len(list(df.columns))} columns.", "success")
    if preview:
        with st.expander('Preview'):
            st.write(df.head(100))
    return df


def df2dict(df:pd.DataFrame, key: str, value: str, select_option: bool=True)->dict:
    """
    returns a dict that can be used in selectboxes. 

    Args:
        df (pd.DataFrame): dataframe includind the columns key and value also specified in the input
        key (str): column name of key in dataframe
        value (str): column name of value in dataframe
        select_option (bool): if true, a -1;<select> entry is added if selection is not mandatory

    Returns:
        dict: key/val dict
    """

    d = dict(zip(list(df[key]), list(df[value])))
    if select_option:
        result = {-1: '<Select>'}
        result.update(d)
    else:
        result = d
    return result


def get_table_download_link(df: pd.DataFrame, message: str, filename: str='downloaded.csv') -> str:
    """
    Generates a link allowing the data in a given panda dataframe to be downloaded

    :param df:          table with data
    :param message:     link text e.g. "click here to download file"
    :return:            link string including the data
    """

    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{message}</a>'
    return href

def list_to_csv_string(value_list:list, prefix: str='', add_quotes: bool=False, sep: str=',')->str:
    """Adds a prefix to each item of a list. Optionally, quotes are added to each item. This is used to generate 
    db query strings when fields from more than one table are queries and identical field names may appear in both tables. 
    example select t1.name, t2.name from xxx as t1, yyy ...

    Args:
        value_list (list): list of field names
        prefix (str): prefix expression, '' if no prefix should be added
        add_quotes (bool): if true, quotes are added to the fields first -> name > t1.name
        sep (str): separator character, default is ','

    Returns:
        str: _description_
    """

    prefix =prefix + '.' if prefix > '' else prefix
    if add_quotes:
        result = [f'{prefix}"{x}"' for x in value_list]
    else:
         result = [f'{prefix}{x}' for x in value_list]
    result = ','.join(result)
    return result