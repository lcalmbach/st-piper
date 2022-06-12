import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

from proj.guideline import Guideline
from proj.parameter import Parameter
import const as cn
import helper
from query import qry
import database as db

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


def exceedance_analysis():
    def get_table(df):
        cols={}
        settings = {'height':400, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
        return helper.show_table(df,cols, settings)

    def show_summary_table(df):
        num_exceedance = len(df[df['exceedance'] == 'yes'])
        num_total = len(df)
        num_non_exceedance = num_total - num_exceedance
        num_nd = len(df[df['value'].str.startswith('<')])
        max_value = df['value_numeric'].max()
        exeeding_stations = df[df['exceedance']=='yes']['station_identifier'].unique() 
        exeeding_stations = ",".join(exeeding_stations)
        st.markdown("**Exceedance Summary**")
        data = [
            ['Number of observations', num_total], 
            ['Number of exceedances', num_exceedance], 
            ['Maximum value', max_value], 
            ['Percent exceedances', format(num_exceedance / num_total * 100 if num_total != 0 else 0, '.1f')], 
            ['Number of detects', num_total-num_nd], 
            ['Percent detects', format(num_exceedance / num_nd * 100 if num_nd != 0 else 0, '.1f')],
            ['Stations with exceedances', exeeding_stations]
        ]
        df_sum = pd.DataFrame(data, columns=['Parameter','Value'])
        layout_cols = st.columns(2)
        cols={}
        settings = {'height':len(df_sum) * cn.AGG_GRID_COL_HEIGHT, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
        with layout_cols[0]:
            helper.show_table(df_sum,cols, settings)
            st.markdown(helper.get_table_download_link(df, '⬇️ Download exceedance summary', filename='exceedance_summary.csv'), unsafe_allow_html=True)

    cfg= st.session_state.user.read_config(cn.EXCEEDANCE_ANALYSIS_ID,'default')
    cfg['guideline'] = helper.get_guideline(cfg['guideline'])
    cfg['prj_parameter'] = helper.get_parameter(cfg['prj_parameter'])
    cfg['filter'] = helper.get_filter(['stations', 'sampling_date'])
    
    parameter = Parameter(cfg['prj_parameter'])
    guideline = Guideline(cfg['guideline'])
    standard = guideline.find_match(parameter)
    st.markdown(f"**Guideline: {guideline.title}**")
    if standard != None:
        st.markdown(f"Detected standard: {parameter.name}: **{standard['max_value']}** {standard['unit']}")
        sql = qry['exceedance_list'].format(standard['max_value'], st.session_state.project.key,parameter.id)
        sql += f" and {cfg['filter']}" if cfg['filter']>'' else ''
        df, ok, err_msg = db.execute_query(query=sql, conn=st.session_state.conn)
        grid_response = get_table(df)
        show_summary_table(df)
    else:
        st.markdown(f"No standard was found for {parameter.name}, this may happen in the case where a standard exists but could not be matched due to a invalid or missing CASNR or simply if the parameter is not included in the guideline. In the first case select the corresponding parameter manually, in the second case enter a value manually if it is known.")
        cols = st.columns([2,2,4])
        standard = {}
        with cols[1]:
            standard['max_value'] = st.text_input(f"Enter maximum tolerated value manually", value=0.000)
        with cols[0]:
            parameter_dict=guideline.get_parameter_dict(allow_none=True)
            sel_standard_id = st.selectbox(label='Select from guideline', options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x])
            if sel_standard_id > 0:
                standard = guideline.get_standard(sel_standard_id)

        if standard != {}:
            sql = qry['exceedance_list'].format(standard['max_value'], st.session_state.project.key, parameter.id)
            sql += f" and {cfg['filter']}" if cfg['filter'] > '' else ''
            df, ok, err_msg = db.execute_query(query=sql, conn=st.session_state.conn)
            st.markdown(f"**Observations for parameter** ***{parameter.name}***")
            grid_response = get_table(df)
            st.markdown(helper.get_table_download_link(df, '⬇️ Download observations', filename='observations.csv'), unsafe_allow_html=True)
            show_summary_table(df)
            


def trend_analyis():
    st.info(f"{__name__} not implemented yet")


def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox('Options', MENU_OPTIONS)
    menu_actions = [exceedance_analysis,
                    trend_analyis]
    id = MENU_OPTIONS.index(menu_action)
    menu_actions[id]()
    