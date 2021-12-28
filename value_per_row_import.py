# from altair.vegalite.v4.schema.core import Interpolate
from st_aggrid import AgGrid
import streamlit as st
import pandas as pd
import numpy as np

import const as cn
import helper


class Value_per_row_import():
    def __init__(self, texts_dict):
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}

        self._step = st.session_state.config.step
        self.texts_dict = texts_dict
        self.file_format = cn.SAMPLE_FORMATS[1]

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, s):
        self._step = s
        st.session_state.config.step = s

    def load_new_dataset(self):
        def load_data():
            df = pd.read_csv(uploaded_file, 
                sep=st.session_state.config.separator, 
                encoding=st.session_state.config.encoding)
            st.success(f"File was loaded: {len(df)} rows, {len(list(df.columns))} columns.")
            with st.expander('Preview'):
                st.write(df.head())
            st.session_state.config.row_value_df = df
        
        def load_config():
            uploaded_column_definition = st.file_uploader("Columns mapping file, csv")
            if uploaded_column_definition:
                st.session_state.config.column_map_df = pd.read_csv(uploaded_column_definition,
                                                                    sep=st.session_state.config.separator)
                with st.expander('Preview columns list'):
                    AgGrid(st.session_state.config.column_map_df)
            uploaded_parameters_definition = st.file_uploader("Parameters mapping file, csv")

            if uploaded_parameters_definition:
                st.session_state.config.parameter_map_df = pd.read_csv(uploaded_parameters_definition,
                                                                       sep=st.session_state.config.separator)
                sample_cols = st.session_state.config.sample_cols()
                station_cols = st.session_state.config.station_cols()
                df, ok = self.unmelt_data(st.session_state.config.row_value_df,
                    st.session_state.config.parameter_col(), 
                    st.session_state.config.value_col(), 
                    sample_cols + station_cols)
                with st.expander('Preview parameter list'):
                    AgGrid(st.session_state.config.parameter_map_df)

        st.title = st.text_input('Dataset title', 'New dataset')
        cols = st.columns(3)
        with cols[0]:
            id = cn.SEPARATORS.index(st.session_state.config.separator)
            st.session_state.config.separator = st.selectbox('Separator character', options=cn.SEPARATORS, index=id)
            # gl_list = st.session_state.config.guideline_list()
            # id = 0
            # st.session_state.config.guidelines[0]['name'] = st.selectbox('Standard/Guideline', options=gl_list, index=id)
        with cols[1]:
            id = cn.ENCODINGS.index(st.session_state.config.encoding)
            st.session_state.config.encoding = st.selectbox('File encoding', options=cn.ENCODINGS, index=id)
        with cols[2]:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox('Date field format', options=cn.DATE_FORMAT_LIST, index=id)
        uploaded_file = st.file_uploader("Data file (csv, 1 row per value format)")
        if uploaded_file is not None:
            load_data()
        
        if st.session_state.config.data_is_loaded():
            load_config_from_file_flag = st.checkbox('Load config from file')

            if load_config_from_file_flag:
                load_config()


    def unmelt_data(self, df, par_col, value_col, group_cols):
        df = pd.pivot_table(df,
            values=value_col,
            index=group_cols,
            columns=par_col,
            aggfunc=np.mean
        ).reset_index()
        ok = len(df) > 0
        return df, ok


    def get_non_matched_options(self, options: list, df: pd.DataFrame()) -> list:
        """Removes the options from the options list, that have already been assigned previously

        Args:
            options (list): list with all options
            df (pd.DataFrame): grid with columns, having a key collumn

        Returns:
            list: list if options that have not been assigned yet
        """
        for idx, col in df.iterrows():
            if (df.loc[idx]['key'] == idx):
                options.remove(idx)
        return options


    def identify_station_columns(self, show_only_matched):
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        with st.expander('Preview'):
            st.dataframe(st.session_state.config.row_value_df.head(100))
        filtered_columns = df[(df['type'] == cn.CTYPE_STATION) | (df['type'].isna())]
        for idx, row in filtered_columns.iterrows():
            if (df.loc[idx]['key'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                id = cn.STATION_COLUMNS_OPTIONS.index(df.loc[idx]['key'])
                df.loc[idx]['key'] = st.selectbox(idx, options=cn.STATION_COLUMNS_OPTIONS, index=id)
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_STATION
                                
                if (df.loc[idx]['key'] == cn.GEOPOINT_COL) and (not st.session_state.config.col_is_mapped(cn.LONGITUDE_COL)):
                    st.session_state.config.geopoint_to_lat_long()


    def identify_sample_columns(self, show_only_matched):
        with st.expander("Preview"):
            st.dataframe(st.session_state.config.row_value_df.head())
        st.session_state.config.has_sample_columns = st.checkbox("Dataset has no sample columns", False)
        df = st.session_state.config.column_map_df
        if not st.session_state.config.has_sample_columns:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox("Sampling date format", options=cn.DATE_FORMAT_LIST, index=id)
            filtered_columns = df[(df['type'] == cn.CTYPE_SAMPLE) | (df['type'].isnull())]
            for idx, col in filtered_columns.iterrows():
                if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                    df.loc[idx]['key'] = st.selectbox(idx, options=cn.SAMPLE_COLUMN_OPTIONS, index=cn.SAMPLE_COLUMN_OPTIONS.index(df.loc[idx]['key']))
                    if df.loc[idx]['key'] == cn.NOT_USED:
                        df.loc[idx]['type'] = None
                    else:
                        df.loc[idx]['type'] = cn.CTYPE_SAMPLE
                    
                    if df.loc[idx]['key'] == cn.SAMPLE_DATE_COL and not st.session_state.config.date_is_formatted:
                        st.session_state.config.format_date_column(df)

                    
    def identify_values_meta_data_columns(self, show_only_matched)->list:
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        filtered_columns = df[(df['type'] == cn.CTYPE_VAL_META) | (df['type'].isnull())]
        options = cn.META_COLUMN_OPTIONS
        for idx, col in filtered_columns.iterrows():
            if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                df.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(df.loc[idx]['key']))
                
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META
                
                if df.loc[idx]['key'] == cn.ND_QUAL_VALUE_COL and not st.session_state.config.value_col_is_filled:
                    ok = st.session_state.config.split_qual_val_column()
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META


    def match_parameters(self, show_only_matched)->str:
        ok, err_msg = True, ''
        casnr_col = st.session_state.config.key2col()[cn.CASNR_COL]
        df_pars = st.session_state.config.parameter_map_df
        if len(df_pars) == 0: 
            st.session_state.config.init_user_parameters()
            st.write('parameters were initialized because none were found')
        
        if casnr_col != None:
            if st.button("Map using CasNR"):
                ok, err_msg = st.session_state.config.map_parameter_with_casnr()

        options = st.session_state.config.lookup_parameters.key2par()
        options = helper.add_not_used2dict(options)
        st.markdown("#### Map parameters")

        for idx, par in df_pars.iterrows():
            # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
            # and an error is thrown

            if not (helper.isnan(par['key']) and show_only_matched):                
                try:
                    id = list(options.keys()).index(par['key'])
                except:
                    id = 0
                if not(show_only_matched) or (par['key'] != cn.NOT_USED):
                    df_pars.loc[idx]['key'] = st.selectbox(idx, options=list(options.keys()), 
                        format_func=lambda x:options[x], 
                        index=id)


    def pivot_table(self):
        def filter_mapped_parameters() -> pd.DataFrame:
            par_col = cols_dict[cn.PARAMETER_COL]
            df = st.session_state.config.parameter_map_df
            df = df.dropna(subset=['key'])
            df = df[df['key'] != cn.NOT_USED]
            lst_parameters = list(df.index)
            
            df_data = st.session_state.config.row_value_df.copy()
            df_data = df_data[df_data[par_col].isin(lst_parameters)]
            return df_data, lst_parameters
        
        def show_settings():
            cols = st.columns([1,4])
            with cols[0]:
                st.markdown('Parameter column:')
                st.markdown('Value column:')
                st.markdown('Sample columns:')
                st.markdown('Station columns:')
            with cols[1]:
                st.markdown(f"{par_col}")
                st.markdown(f"{value_col}")
                st.markdown(f"{','.join(sample_cols)}")
                st.markdown(f"{','.join(station_cols)}")
        
        cols_dict = st.session_state.config.key2col()
        par_col = st.session_state.config.parameter_col()
        value_col = st.session_state.config.value_col()
        sample_cols = st.session_state.config.sample_cols()
        station_cols = st.session_state.config.station_cols()
        sample_cols = sample_cols + station_cols
        show_settings()
        
        use_only_matched_parameters = st.checkbox("Use only matched parameters")
        if use_only_matched_parameters:
            df, used_parameters = filter_mapped_parameters()
        else:
            df = st.session_state.config.row_value_df
            used_parameters = list(st.session_state.config.parameter_map_df.index)
        with st.expander("Used measured parameters"):
            st.dataframe(used_parameters)
        if st.button("Unmelt table"):
            df, ok = self.unmelt_data(df, par_col, value_col, sample_cols)
            if ok:
                parameter_master_data = st.session_state.config.lookup_parameters.metadata_df
                df = helper.complete_columns(df, st.session_state.config.key2par(), parameter_master_data)
                df.to_csv('data.csv', sep=st.session_state.config.separator)
                st.success("data was successfully transformed")
                AgGrid(df.head(100))
            st.session_state.config.row_sample_df = df

            st.session_state.config.column_map_df.to_csv('columns.csv', sep=st.session_state.config.separator)
            st.session_state.config.parameter_map_df.to_csv('parameters.csv', sep=st.session_state.config.separator)


    def run_step(self):
        steps = self.texts_dict['steps']
        option_item_sel = st.sidebar.selectbox('Import steps', steps)
        self.step = steps.index(option_item_sel)
        show_only_matched = st.sidebar.checkbox("Show only matched parameters")
        
        title = self.texts_dict[f"step{self.step}_title"]
        info = self.texts_dict[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        if self.step == 0:
            self.load_new_dataset()
        elif self.step == 1:
            self.identify_station_columns(show_only_matched)
        elif self.step == 2:
            self.identify_sample_columns(show_only_matched)
        elif self.step == 3:
            self.identify_values_meta_data_columns(show_only_matched)
        elif self.step == 4:
            self.match_parameters(show_only_matched)
        elif self.step == 5:
            self.pivot_table()
            

