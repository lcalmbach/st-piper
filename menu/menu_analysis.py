import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np

from proj.guideline import Guideline
from proj.parameter import Parameter
from proj.guideline import Standard
from proj.phreeqc_simulation import PhreeqcSimulation
import const as cn
import helper
from query import qry
import proj.database as db
import pymannkendall as mk
import altair as alt

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
        st.markdown(f"Detected standard: {parameter.name}: **{standard.max_value}** {standard.unit}")
        sql = qry['exceedance_list'].format(standard.max_value, st.session_state.project.key,parameter.id)
        sql += f" and {cfg['filter']}" if cfg['filter']>'' else ''
        df, ok, err_msg = db.execute_query(query=sql, conn=st.session_state.conn)
        grid_response = get_table(df)
        show_summary_table(df)
    else:
        st.markdown(f"No standard was found for {parameter.name}, this may happen in the case where a standard exists but could not be matched due to a invalid or missing CASNR or simply if the parameter is not included in the guideline. In the first case select the corresponding parameter manually, in the second case enter a value manually if it is known.")
        cols = st.columns([2,2,4])
        standard = None
        with cols[0]:
            parameter_dict=guideline.get_parameter_dict(allow_none=True)
            sel_standard_id = st.selectbox(label='Select from guideline', options=list(parameter_dict.keys()), 
                                            format_func=lambda x:parameter_dict[x])
            if sel_standard_id > 0:
                standard = guideline.get_standard(sel_standard_id)

        with cols[1]:
            if standard != None:
                default_value = standard.max_value
            else:
                default_value = 0
                standard = Standard(None, None)
            standard.max_value = st.text_input(f"Enter maximum tolerated value manually", value=default_value)

        
        sql = qry['exceedance_list'].format(standard.max_value, st.session_state.project.key, parameter.id)
        sql += f" and {cfg['filter']}" if cfg['filter'] > '' else ''
        df, ok, err_msg = db.execute_query(query=sql, conn=st.session_state.conn)
        st.markdown(f"**Observations for parameter** ***{parameter.name}, {len(df[df['exceedance']=='yes'])}/{len(df)} exceedances***")
        grid_response = get_table(df)
        st.markdown(helper.get_table_download_link(df, '⬇️ Download observations', filename='observations.csv'), unsafe_allow_html=True)
        show_summary_table(df)


def mann_kendall_trend_analyis():
    def execute_trend_analysis(df:pd.DataFrame, cfg):
        def mk_res2df(res):
            df = pd.DataFrame(data = {'par':['alpha','trend-result','p-value','z','Tau','s','slope','intercept'],
                'value':[cfg['alpha'],res.trend,res.p,res.z,res.Tau,res.s,res.slope,res.intercept]})
            return df
    
        values = list(df['value_numeric'])
        res = mk.original_test(values, alpha=cfg['alpha'])
        res_df = mk_res2df(res)
        cols={}
        settings = {'height':len(res_df) * cn.AGG_GRID_COL_HEIGHT, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
        st.markdown(f"**{cfg['title']}**")
        st.markdown(f"Test result: {res.trend}")
        columns = st.columns([1,3])
        with columns[0]:
            helper.show_table(res_df, cols, settings)
            trend_line = np.arange(len(df)) * res.slope + res.intercept
            df['trend_line']=trend_line
            
        with columns[1]:
            show_time_series_plot(df, cfg)
        with st.expander("View values"):
            cols={}
            settings = {'height':len(df) * cn.AGG_GRID_COL_HEIGHT, 'selection_mode':'single', 'fit_columns_on_grid_load': False}
            helper.show_table(df, cols, settings)


    def show_time_series_plot(df:pd.DataFrame, cfg: dict):
        x_domain = [f"{df['sampling_date'].min().year}-01-01", f"{df['sampling_date'].max().year}-12-31"]
        y_domain = helper.get_domain(df,'value_numeric')
        
        chart = alt.Chart(df).mark_line(width = 20, point=alt.OverlayMarkDef(color='blue', opacity=0.6)).encode(
            x = alt.X('sampling_date:T', scale=alt.Scale(domain=x_domain), axis=alt.Axis(title='')),
            y= alt.Y('value_numeric:Q', scale=alt.Scale(domain=y_domain)),
            tooltip=['sampling_date', 'value_numeric']
        )
        regr_line = chart.transform_regression('sampling_date', 'value_numeric').mark_line(color='green')
        trend_line = alt.Chart(df).mark_line(width = 20, strokeDash=[1,1], color='magenta').encode(
            x = alt.X('sampling_date:T'),
            y= alt.Y('trend_line:Q')
        )
        if cfg['show_sen_trend']:
            chart = chart + regr_line
        if cfg['show_sen_trend']:
            chart = chart + trend_line
        chart = (chart).properties(width=800, height = 200, title = cfg['title'])
        st.altair_chart(chart)


    def get_settings(cfg):
        with st.sidebar.expander(f"⚙️{lang['settings']}"):
            options = lang['detail_summary']
            x = st.radio(label='Output', options=options)
            cfg['output'] = options.index(x)
            if cfg['output'] == 0:
                cfg['show_sen_trend'] = st.checkbox(label=lang['show_sen_line'])
                cfg['show_regresssion'] = st.checkbox(label=lang['show_regression_line'])
        return cfg
    
    cfg = st.session_state.user.read_config(cn.TREND_ANALYSIS_ID,'default')
    cfg['prj_parameter'] = helper.get_parameter(cfg['prj_parameter'])
    parameter = Parameter(cfg['prj_parameter'])
    cfg['alpha']= 0.05
    cfg['stations'] = helper.get_stations(cfg['stations'], '')
    cfg = get_settings(cfg)
    proj = st.session_state.project
    df = proj.time_series(cfg['prj_parameter'], cfg['stations'] )
    if st.sidebar.button("Run analysis"):
        for station_id in cfg['stations']:
            cfg['title'] = lang['result_title'].format(parameter.name, station_id)
            df_filtered = df.query('station_id == @station_id')
            execute_trend_analysis(df_filtered, cfg)


def saturation_analysis():
    def phreeqc_analysis(df):
        import os
        filename = 'vitens.dat'
        phr_sim = PhreeqcSimulation(st.session_state.project, therm_db=st.session_state.project.phreeqc_database)
        with st.spinner("running phreeqc"):
            for index, row in df.iterrows():
                identifiers={'station': row['station_identifier'], 'date': row['sampling_date']}
                df_sample = st.session_state.project.phreeqc_observations(row['sample_number'])
                s = phr_sim.add_solution(df_sample, identifiers)
        return phr_sim
            
    def get_filter(stations, from_date, to_date):
        filter = ''
        stations = [str(x) for x in stations]
        filter += f"where station_id in ({','.join(stations)}) " if stations != [] else ''
        filter += " WHERE " if filter == '' else ' AND ' 
        filter += f"sampling_date between '{from_date}' and '{to_date}'"
        return filter

    cfg = st.session_state.user.read_config(cn.SATURATION_ANALYSIS_ID,'default')
    cfg['stations'] = helper.get_stations(cfg['stations'], '')
    cfg['date_from'] = st.sidebar.date_input('Date from')
    cfg['date_to'] = st.sidebar.date_input('Date to')
    proj = st.session_state.project
    filter = get_filter(cfg['stations'], cfg['date_from'], cfg['date_to'])
    df = proj.phreeqc_samples(filter)
    cols={}
    settings = {'height':helper.get_grid_height(df,300), 'selection_mode':'multiple', 'fit_columns_on_grid_load': False}
    selected_samples = helper.show_table(df, cols, settings)

    if st.button("Start analysis"):
        if len(selected_samples)==0:
            phr_sim = phreeqc_analysis(df)
        else:
            phr_sim = phreeqc_analysis(selected_samples)
        df = phr_sim.get_phase_df()
        st.markdown(f"### {lang['calc_sat_ind']}")
        settings = {'height':helper.get_grid_height(df,400), 'selection_mode':'single', 'fit_columns_on_grid_load': False}
        sel_row = helper.show_table(df, cols, settings)
        st.markdown(helper.get_table_download_link(df, '⬇️ Download saturation table', filename='phreeqc_output_saturation.csv'), unsafe_allow_html=True)
        if len(sel_row)>0:
            st.write(phr_sim.get_solution())

def show_menu():
    set_lang()
    MENU_OPTIONS = lang['menu_options']
    menu_action = st.sidebar.selectbox(label='Options', options=MENU_OPTIONS)
    menu_actions = [exceedance_analysis, mann_kendall_trend_analyis, saturation_analysis]
    id = MENU_OPTIONS.index(menu_action)
    menu_actions[id]()
    