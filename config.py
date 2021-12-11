import const as cn
import pandas as pd
import uuid
import streamlit as st

from metadata import Metadata


class Config():
    def __init__(self):
        self.title = ''
        self.encoding = cn.ENCODINGS[0]
        self.separator = cn.SEPARATORS[0]
        self.date_format = cn.DATE_FORMAT_LIST[0]
        self.row_sample_df = pd.DataFrame()
        self.row_value_df = pd.DataFrame()
        self._column_map_df = pd.DataFrame({'column_name': [], 'key': []})
        self._parameter_map_df = pd.DataFrame({'parameter': [], 'casnr': [], 'key': []})
        self.guidelines = [{'name': self.guideline_list()[0], 'data': self.read_guideline(self.guideline_list()[0])}]
        self.load_config_from_file_flag = False
        self.file_format = ''
        self.date_is_formatted = False
        self.params_params_valid = False
        self.sessionid = uuid.uuid1()
        self.lookup_parameters = Metadata() # metadata for a wide selection of parameters 
        # self.current_dataset = get_data()
        self.piper_config = cn.piper_cfg
        self.time_stations_config = {}
        self.time_parameters_config = {}
        self.map_parameters_config = {}
        
        self.step = 0
        # true if either the value column is mapped or if the qual-value col is mapped and 
        # the value and detection-flag column is generated
        self.value_col_is_filled: bool = False 
        # true if either the qual-value column is mapped or if the value and qual cols are mapped and 
        # the qual-value is generated

    @property
    def column_map_df(self):
        return self._column_map_df
       
    @column_map_df.setter
    def column_map_df(self, column_map):
        self._column_map_df = column_map
        self._column_map_df.set_index('column_name', inplace=True)

        if self.col_is_mapped(cn.SAMPLE_DATE_COL):
            self.format_date_column()
        if self.col_is_mapped(cn.GEOPOINT_COL):
            self.geopoint_to_lat_long()
        if self.col_is_mapped(cn.ND_QUAL_VALUE_COL):
            self.split_qual_val_column()


    @property
    def parameter_map_df(self):
        return self._parameter_map_df
       
    @parameter_map_df.setter
    def parameter_map_df(self, parameter_map):
        self._parameter_map_df = parameter_map
        self._parameter_map_df.set_index('parameter', inplace=True)

# functions-----------------------------------------------------------------------------------------

    def guideline_list(self):
        return ['epa_mcl']

    def read_guideline(self, gl:str):
        filename = f"{cn.GUIDELINE_ROOT}{gl}.csv"
        return pd.read_csv(filename, sep='\t')

    def init_column_map(self):
        ok, err_msg = True, ''
        try:
            df = pd.DataFrame({'column_name': list(self.row_value_df)})
            df['key'] = cn.NOT_USED
            df['type'] = None
            self.column_map_df = df
        except:
            ok = False
            err_msg = 'Column map could not be initialized'
        return ok

    def get_menu_options(self):
        result = {0: "Info", 1: "Load data"}
        if self.columns_are_mapped() and self.parameters_are_mapped():
            result[2] = "Samples"
            result[3] = "Stations"
            result[4] = "Parameters"
            result[5] = "Plots"
        return result
    
    def get_plots_options(self):
        result = []
        if self.col_is_mapped(cn.SAMPLE_DATE_COL):
            result.append("Time series")
        if self.col_is_mapped(cn.LATITUDE_COL):
            result.append("Maps")
        if self.major_ions_complete():
            result.append("Piper plots")
        return result

    def par_is_mapped(self, key_name):
        ok = key_name in list(self.parameter_map_df['key']) if len(self.parameter_map_df) > 0 else False
        return ok

    def col_is_mapped(self, key_name):
        ok = key_name in list(self.column_map_df['key']) if len(self.column_map_df) > 0 else False
        return ok

    def coltype2dict(self, col_type):
        df = self.column_map_df[self.column_map_df['type'] == col_type]
        result = zip(list(df.index), list(df.key))
        return dict(result)

    def col2key(self) -> dict:
        result = zip(list(self.column_map_df.index), list(self.column_map_df.key))
        return dict(result)


    def key2col(self) -> dict:
        df = self.column_map_df[self.column_map_df['key'] != cn.NOT_USED]
        result = zip(list(df['key']), list(df.index))
        return dict(result)


    def par2key(self) -> dict:
        result = zip(list(self.parameter_map_df.index), list(self.parameter_map_df.key))
        return dict(result)


    def key2par(self)->dict:
        df = self.parameter_map_df[self.parameter_map_df['key'] != cn.NOT_USED]
        result = zip(list(df['key']), list(df.index))
        return dict(result)


    def merge_qual_val_column(self):
        """if value and qualifier are mapped in seperate columns, these 2 columns are additionall merged in
        a common column e.g. | < | 0.05 | becomes <0.05

        Returns:
            [type]: [description]
        """
        ok = False
        val_col = self.key2col()[cn.VALUE_NUM_COL]
        qual_col = self.key2col()[cn.ND_QUAL_COL]
        if qual_col != None:
            val_qual_col = '_qual_value'
            self.row_value_df[val_qual_col] = ''  
            self.row_value_df.loc[self.row_value_df[qual_col]=='<',val_qual_col] = self.row_value_df[qual_col] + self.row_value_df[val_col]
        
        self.value_col_is_filled = True
        ok = True
        return ok

    def split_qual_val_column(self):
        ok = False
        qual_val_col = self.key2col()[cn.ND_QUAL_VALUE_COL]
        nd_flag_col = cn.ND_FLAG_COL
        df = self.row_value_df

        df[qual_val_col] = df[qual_val_col].astype(str)
        df[nd_flag_col] = False
        df.loc[df[qual_val_col].str.startswith('<') == True, nd_flag_col] = True
        df.loc[df[nd_flag_col] == True, cn.VALUE_NUM_COL] = df[qual_val_col].str.replace('<', '')
        df.loc[(df[nd_flag_col] == False), cn.VALUE_NUM_COL] = pd.to_numeric(df[qual_val_col],errors='coerce') 
        df[cn.VALUE_NUM_COL] = df[cn.VALUE_NUM_COL].astype('float') 
        df.loc[(df[nd_flag_col] == True) & (df[cn.VALUE_NUM_COL] != 0), cn.VALUE_NUM_COL] = df[cn.VALUE_NUM_COL] / 2
        self.column_map_df.loc[cn.VALUE_NUM_COL] = [cn.VALUE_NUM_COL, cn.CTYPE_VAL_META]
        self.qual_value_col_is_filled = True
        ok = True
        return ok


    def format_date_column(self):
        ok = False
        date_col = self.key2col()[cn.SAMPLE_DATE_COL]
        try:
            self.row_value_df[date_col] = pd.to_datetime(self.row_value_df[date_col], format=self.date_format, errors='ignore')
            ok = True
        except:
            pass
        return ok


    def stations_params_valid(self):
        result = cn.STATION_IDENTIFIER_COL in list(self.column_map_df['key'])
        return result
    
    def sample_params_valid(self):
        result = cn.SAMPLE_IDENTIFIER_COL in list(self.column_map_df['key']) 
        result = result or cn.SAMPLE_DATE_COL in list(self.column_map_df['key'])
        return result

    def meta_params_valid(self):
        result = cn.VALUE_COL in list(self.column_map_df['key'])
        result = result or cn.DESC_VALUE_COL in list(self.column_map_df['key'])
        result = result and cn.PARAMETER_COL in list(self.column_map_df['key'])

    def has_casnr(self):
        """
        Returns true if casnr and parameter key has been mapped.

        Returns:
            [type]: [description]
        """
        result = cn.CASNR_COL in list(self.column_map_df['key'])
        result = result and cn.PARAMETER_COL in list(self.column_map_df['key'])
        return result

    def geopoint_to_lat_long(self):
        ok,err_msg = True,''
        col_name = self.key2col()[cn.GEOPOINT_COL]
        df = self.row_value_df
        df[['latitude', 'longitude']] = df[col_name].str.split(',', expand=True)
        df = self.column_map_df
        df.loc[cn.LATITUDE_COL.lower()] = [cn.LATITUDE_COL.lower(), cn.CTYPE_STATION]
        df.loc[cn.LONGITUDE_COL.lower()] = [cn.LONGITUDE_COL.lower(), cn.CTYPE_STATION]
        return ok, err_msg

    def get_parameter_detail_form_columns(self):
        """Returns a list of columns used to display a single sample depending on what columns have been
        mapped. 

        Returns:
            [type]: [description]
        """
        lst_cols = [self.key2col()[cn.PARAMETER_COL]]
        if self.col_is_mapped(cn.UNIT_COL):
            lst_cols.append(self.key2col()[cn.UNIT_COL])
        if self.col_is_mapped(cn.CASNR_COL):
            lst_cols.append(self.key2col()[cn.CASNR_COL])
        if self.col_is_mapped(cn.ND_QUAL_VALUE_COL):
            lst_cols.append(self.key2col()[cn.ND_QUAL_VALUE_COL])
            lst_cols.append(self.key2col()[cn.VALUE_NUM_COL])
        if self.col_is_mapped(cn.DL_COL):
            lst_cols.append(self.key2col()[cn.DL_COL])
            lst_cols.append(self.key2col()[cn.VALUE_NUM_COL])
        if self.col_is_mapped(cn.CATEGORY_COL):
            lst_cols.append(self.key2col()[cn.CATEGORY_COL])
        if self.col_is_mapped(cn.COMMENT_COL):
            lst_cols.append(self.key2col()[cn.COMMENT_COL])
        return lst_cols


    def init_user_parameters(self):
        parameter_col = self.key2col()[cn.PARAMETER_COL]
        casnr_col = self.key2col()[cn.CASNR_COL]

        if casnr_col != None:
            df_pars = pd.DataFrame(self.row_value_df[[parameter_col, casnr_col]].drop_duplicates())
            df_pars.columns = ['parameter', 'casnr']
            df_pars['key'] = cn.NOT_USED
            st.session_state.config.parameter_map_df = df_pars
            print('here')
        elif casnr_col == None:
            df_pars = pd.DataFrame(self.row_value_df[[parameter_col]].drop_duplicates())
            df_pars.columns = ['parameter']
            df_pars['key'] = cn.NOT_USED
            st.session_state.config.parameter_map_df = df_pars  
            print('there')
    
    def map_parameter_with_casnr(self)->pd.DataFrame():
        """use mapped casnr fields in order to identify parameters automatically using 
           the internal database table.

        Args:
            df (pd.DataFrame): [description]

        Returns:
            pd.DataFrame: column dataframe with matched parameters where valid 
            casnr is available
        """

        ok, err_msg = True, ''
        result_df = self.parameter_map_df.copy().reset_index()
        df_casnr = st.session_state.config.lookup_parameters.metadata_df.reset_index()
        df_casnr = df_casnr[df_casnr.casnr.notnull()]
        df_casnr = df_casnr[['key','casnr']]
        result_df = pd.merge(result_df, df_casnr, left_on='casnr', right_on='casnr', how='left')
        result_df = result_df[['parameter', 'casnr', 'key_y']]
        result_df.columns = ['parameter', 'casnr', 'key']
        # set all rows where key = null to string 'not used'
        result_df = result_df.fillna(value={'key': cn.NOT_USED})
        self.parameter_map_df = result_df
        return ok, err_msg

    def major_ions_complete(self):
        ok = (self.par_is_mapped(cn.PAR_CALCIUM)
                and self.par_is_mapped(cn.PAR_MAGNESIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_ALKALINITY)
                and self.par_is_mapped(cn.PAR_SULFATE)
                and self.par_is_mapped(cn.PAR_CHLORIDE))
        return ok

    def get_station_list(self):
        station_key = self.key2col()[cn.STATION_IDENTIFIER_COL]
        result = list(self.row_value_df[station_key].unique())
        return result

    def data_is_loaded(self) -> bool:
        return (len(self.row_sample_df)>0) | (len(self.row_value_df)> 0)

    def columns_are_mapped(self) -> bool:
        return self.col_is_mapped(cn.STATION_IDENTIFIER_COL)
    
    def parameters_are_mapped(self) -> bool:
        df = self.parameter_map_df
        return len(df[df['key'] != cn.NOT_USED]) > 0
    
    def parameter_col(self) -> str:
        return st.session_state.config.key2col()[cn.PARAMETER_COL]
    
    def station_identifier_col(self) -> str:
        return st.session_state.config.key2col()[cn.STATION_IDENTIFIER_COL]

    def sample_identifier_col(self) -> str:
        if self.col_is_mapped(cn.SAMPLE_IDENTIFIER_COL):
            return st.session_state.config.key2col()[cn.SAMPLE_IDENTIFIER_COL]
        elif self.col_is_mapped(cn.DATE_IDENTIFIER_COL):
            return st.session_state.config.key2col()[cn.DATE_IDENTIFIER_COL]
        else:
            return None
    
    def value_col(self) -> str:
        return st.session_state.config.key2col()[cn.VALUE_NUM_COL]

    def sample_cols(self) -> list:
        return list(st.session_state.config.coltype2dict(cn.CTYPE_SAMPLE).keys())
    
    def station_cols(self) -> list:
        return list(st.session_state.config.coltype2dict(cn.CTYPE_STATION).keys())

    def date_col(self) -> str:
        return st.session_state.config.coltype2dict(cn.cn.SAMPLE_DATE_COL)

    def parameter_categories(self):
        if self.col_is_mapped(cn.CATEGORY_COL):
            pc_col_name = self.key2col()[cn.CATEGORY_COL]
            return list(self.row_value_df[pc_col_name].unique())
        else:
            return []
    
    def get_standards(self, parameter):
        casnr = self.parameter_map_df.loc[parameter]['casnr']
        result = []
        for guideline in self.guidelines:
            df = guideline['data']
            value = df.query('casnr == @casnr')
            if len(value) > 0:
                result.append({'name': guideline['name'],
                               'value': value.iloc[0]['value'],
                               'unit': value.iloc[0]['unit']
                })
        return result


