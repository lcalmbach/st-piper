class Config():
    def __init__(self):
        self.language = 'en'
        lang = helper.get_language(__name__, self.language)
        self.session_key = uuid.uuid1()
        self.logged_in_user = None
        self.pwd = None
        self.title = ''
        self.encoding = cn.ENCODINGS[0]
        self.separator = cn.SEPARATORS[0]
        self.date_format = cn.DATE_FORMAT_LIST[0]
        self.preferred_date_format = '%d/%m/%Y'
        self._row_sample_df = pd.DataFrame()
        self._row_value_df = pd.DataFrame()
        self._column_map_df = pd.DataFrame({'column_name': [], 'key': []})
        self._parameter_map_df = pd.DataFrame({'parameter': [], 'casnr': [], 'key': []})
        self.load_config_from_file_flag = False
        self.file_format = ''
        self.date_is_formatted = False
        self.params_params_valid = False
        self.lookup_parameters = Metadata() # metadata for a wide selection of parameters 
        self.time_stations_config = {}
        self.time_parameters_config = {}
        self.map_parameters_config = {}
        self.projects_df = self.get_projects()
        self.unit_row = 1

        self._project = {}
        self.user = User('x')
        
        self.step = 0
        # true if either the value column is mapped or if the qual-value col is mapped and 
        # the value and detection-flag column is generated
        self.value_col_is_filled: bool = False 
        # true if either the qual-value column is mapped or if the value and qual cols are mapped and 
        # the qual-value is generated

# properties---------------------------------------------------------------------------------------
    @property
    def project_dict(self)->dict:
        df = pd.DataFrame(self.projects_df)
        dic = dict(zip(df['id'], df['title']))
        return dic

    @property
    def project(self):
        return self._project
       
    @project.setter
    def project(self, prj:Project):
        self._project = prj

    @property
    def row_sample_df(self):
        return self._row_sample_df
       
    @row_sample_df.setter
    def row_sample_df(self, df):
        self._row_sample_df = df
        if self.major_ions_complete:
            df = helper.complete_columns(df, self.key2par(), self.lookup_parameters.metadata_df)

    @property
    def row_value_df(self):
        return self._row_value_df
       
    @row_value_df.setter
    def row_value_df(self, df):
        self._row_value_df = df
        self.init_column_map()

    @property
    def column_map_df(self):
        return self._column_map_df
       
    @column_map_df.setter
    def column_map_df(self, column_map):
        self._column_map_df = column_map
        self._column_map_df.set_index('column_name', inplace=True)
        self.check_columns()
        
    @property
    def parameter_map_df(self):
        return self._parameter_map_df
       
    @parameter_map_df.setter
    def parameter_map_df(self, parameter_map):
        self._parameter_map_df = parameter_map
        self._parameter_map_df.set_index('parameter', inplace=True)

    @property
    def longitude_col(self) -> str:
        return self.key2col()[cn.LONGITUDE_COL]

    @property
    def latitude_col(self) -> str:
        return self.key2col()[cn.LATITUDE_COL]

    @property
    def station_col(self) -> str:
        return self.key2col()[cn.STATION_IDENTIFIER_COL]

    @property
    def parameter_col(self) -> str:
        return self.key2col()[cn.PARAMETER_COL]

    @property
    def value_col(self) -> str:
        return self.key2col()[cn.VALUE_NUM_COL]

    @property
    def sample_cols(self) -> list:
        return list(self.coltype2dict(cn.CTYPE_SAMPLE).keys())
    
    @property
    def station_cols(self) -> list:
        return list(self.coltype2dict(cn.CTYPE_STATION).keys())
    
    @property
    def sample_station_cols(self) -> list:
        """
        returns the list of all station and sample related parameters. Often, these are used to for grouping
        """
        fields = self.sample_cols
        fields += self.station_cols
        return fields

    @property
    def parameter_list(self) -> list:
        return list(self.parameter_map_df.index)

    @property
    def date_col(self) -> str:
        return self.key2col()[cn.SAMPLE_DATE_COL]

    @property
    def sample_identifier_col(self) -> str:
        if self.col_is_mapped(cn.SAMPLE_IDENTIFIER_COL):
            return self.key2col()[cn.SAMPLE_IDENTIFIER_COL]
        elif self.col_is_mapped(cn.DATE_IDENTIFIER_COL):
            return self.key2col()[cn.DATE_IDENTIFIER_COL]
        else:
            return None
    @property
    def major_ions_complete(self):
        ok = (self.par_is_mapped(cn.PAR_CALCIUM)
                and self.par_is_mapped(cn.PAR_MAGNESIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_ALKALINITY)
                and self.par_is_mapped(cn.PAR_SULFATE)
                and self.par_is_mapped(cn.PAR_CHLORIDE))
        return ok
    
    @property
    def logged_in_user_name(self):
        return 'please login'if self.logged_in_user == None else self.logged_in_user


# functions----------------------------------------------------------------------------------------
    def get_guideline_dict(self)->pd.DataFrame:
        sql = qry['guidelines']
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        result = dict(zip(df['id'], df['title']))
        return result
    

    def get_projects(self)->pd.DataFrame:
        if self.is_logged_in():
            sql = qry['user_projects'].format(self.user.id)
        else:
            sql = qry['public_projects']
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
        
    def check_columns(self):
        """
        sets the format of matched columns such as date column. This is only possible if the sample_row df 
        exists. todo: call this for each dataframe : values as row and sample. then the columns are fixed when they are present
        """
        if len(self._row_value_df) > 0:
            if self.col_is_mapped(cn.SAMPLE_DATE_COL):
                self.format_date_column(self._row_value_df)
            if self.col_is_mapped(cn.GEOPOINT_COL):
                self.geopoint_to_lat_long(self._row_value_df)
            if self.col_is_mapped(cn.ND_QUAL_VALUE_COL):
                self.split_qual_val_column()
            if self.col_is_mapped(cn.LATITUDE_COL):
                self._row_value_df[self.latitude_col] = self._row_value_df[self.latitude_col].astype(float)
                self._row_value_df[self.longitude_col] = self._row_value_df[self.longitude_col].astype(float)
        
        # same for row as sample format datafram
        if len(self._row_sample_df) > 0:
            if self.col_is_mapped(cn.SAMPLE_DATE_COL):
                self.format_date_column(self._row_sample_df)
                if not 'year' in self._row_sample_df.columns:
                    self._row_sample_df['year'] = self._row_sample_df[self.date_col].dt.year
            if self.col_is_mapped(cn.LATITUDE_COL):
                self._row_sample_df[self.latitude_col] = self._row_sample_df[self.latitude_col].astype(float)
                self._row_sample_df[self.longitude_col] = self._row_sample_df[self.longitude_col].astype(float)


        def import_row_value():
            def pivot_data():
                sample_cols = self.sample_cols
                station_cols = self.station_cols
                group_cols = sample_cols + station_cols
                self.row_sample_df = pd.pivot_table(self.row_value_df,
                    values=self.value_col,
                    index=group_cols,
                    columns=self.parameter_col,
                    aggfunc=np.mean
                ).reset_index()

            # read the data
            folder = Path("data/")
            self.date_format = self.project.date_format
            self.row_value_df = pd.read_csv(folder / data_file(), 
                                            sep=self.project.separator, 
                                            encoding=self.project.encoding)
            # read column mapping
            self.column_map_df = pd.read_csv(folder / column_map_file(), sep=';')

            # read parameter mapping
            self.parameter_map_df = pd.read_csv(folder / parameter_map_file(), sep=';')
            pivot_data()

        def import_row_sample():
            """
            data in the format 1 row per sample are melted to the format 1 row per value: the values are grouped by station 
            and sample fields. the additional parameter rows each build a new row per row.
            """

            def melt_data():
                df = pd.melt(frame=self.row_sample_df,
                                             id_vars=self.sample_station_cols, 
                                             value_vars = self.parameter_list,
                                             var_name = 'parameter',
                                             value_name = 'value'
                )
                df['unit'] = ''
                df['detection_limit'] = 0
                return df


            # read the data
            folder = Path("data/")
            self.date_format = self.project.date_format
            self.row_sample_df = pd.read_csv(folder / data_file(), 
                                            sep=self.project.separator, 
                                            encoding=self.project.encoding)
            # read column mapping
            self.column_map_df = pd.read_csv(folder / column_map_file(), sep=';')
            df = self.column_map_df
            df = df[df['type'].isin(['sa', 'st'])]
            df.loc['parameter'] = [cn.PARAMETER_COL, cn.CTYPE_VAL_META, None]
            df.loc['value'] = [cn.ND_QUAL_VALUE_COL, cn.CTYPE_VAL_META, None]
            df.loc['num_value'] = [cn.VALUE_NUM_COL, cn.CTYPE_VAL_META, None]
            df.loc['unit'] = [cn.UNIT_COL, cn.CTYPE_VAL_META, None]
            df.loc['detection_limit'] = [cn.DL_COL, cn.CTYPE_VAL_META, None]
            self.column_map_df = df.reset_index()
            
            # read parameter mapping
            self.parameter_map_df = pd.read_csv(folder / parameter_map_file(), sep=';')
            self._row_value_df = melt_data()
            # trigger set column map, since only now all information is available. this triggers the formatting of essential 
            # columns such as date
            self.check_columns()
            

    def read_all_guidelines(self):
        with open(f"{cn.GUIDELINE_ROOT}guidelines.json") as f:
            guidelines_df = pd.DataFrame(json.load(f))
        return guidelines_df

    def read_guideline_data(self):
        data = pd.DataFrame()
        for index, row in self.guidelines_df.iterrows():
            filename = f"{cn.GUIDELINE_ROOT}{row['filename']}"
            df =  pd.read_csv(filename, sep='\t')
            df['key'] = row['key']
            data = data.append(df, ignore_index=True)
        return data
    
    def get_plots_options(self):
        result = []
        result.append("Scatter")
        result.append("Histogram")
        result.append("Boxplot")
        if self.col_is_mapped(cn.SAMPLE_DATE_COL):
            result.append("Time series")
        if self.col_is_mapped(cn.LATITUDE_COL):
            result.append("Map")
        if self.major_ions_complete:
            result.append("Piper")
            result.append("Schoeller")

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

    def par2casnr(self) -> dict:
        result = zip(list(self.parameter_map_df.index), list(self.parameter_map_df.casnr))
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
        self.column_map_df.loc[cn.VALUE_NUM_COL] = [cn.VALUE_NUM_COL, cn.CTYPE_VAL_META, None]
        self.qual_value_col_is_filled = True
        ok = True
        return ok


    def format_date_column(self, df):
        ok = False
        try:
            df[self.date_col] = pd.to_datetime(df[self.date_col], format=self.date_format, errors='ignore')
            print('date column was formatted')
            ok = True
        except:
            print('date column could not be formatted')
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

    def geopoint_to_lat_long(self, df):
        ok,err_msg = True,''
        col_name = self.key2col()[cn.GEOPOINT_COL]
        df[[cn.LATITUDE_COL, cn.LONGITUDE_COL]] = df[col_name].str.split(',', expand=True)
        df = self.column_map_df
        df.loc[cn.LATITUDE_COL] = [cn.LATITUDE_COL, cn.CTYPE_STATION, None]
        df.loc[cn.LONGITUDE_COL] = [cn.LONGITUDE_COL, cn.CTYPE_STATION, None]
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

        casnr_col = self.key2col()[cn.CASNR_COL]

        if casnr_col != None:
            df_pars = pd.DataFrame(self.row_value_df[[self.parameter_col, casnr_col]].drop_duplicates())
            df_pars.columns = ['parameter', 'casnr']
            df_pars['key'] = cn.NOT_USED
            self.parameter_map_df = df_pars
        elif casnr_col == None:
            df_pars = pd.DataFrame(self.row_value_df[[self.parameter_col]].drop_duplicates())
            df_pars.columns = ['parameter']
            df_pars['key'] = cn.NOT_USED
            self.parameter_map_df = df_pars  
    
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
        df_casnr = self.lookup_parameters.metadata_df.reset_index()
        df_casnr = df_casnr[df_casnr.casnr.notnull()]
        df_casnr = df_casnr[['key','casnr']]
        result_df = pd.merge(result_df, df_casnr, left_on='casnr', right_on='casnr', how='left')
        result_df = result_df[['parameter', 'casnr', 'key_y']]
        result_df.columns = ['parameter', 'casnr', 'key']
        # set all rows where key = null to string 'not used'
        result_df = result_df.fillna(value={'key': cn.NOT_USED})
        self.parameter_map_df = result_df
        return ok, err_msg



    def data_is_loaded(self) -> bool:
        return (len(self.row_sample_df)>0) | (len(self.row_value_df)> 0)

    def columns_are_mapped(self) -> bool:
        return self.col_is_mapped(cn.STATION_IDENTIFIER_COL)
    
    def parameters_are_mapped(self) -> bool:
        df = self.parameter_map_df
        return len(df[df['key'] != cn.NOT_USED]) > 0

    def parameter_categories(self):
        if self.col_is_mapped(cn.CATEGORY_COL):
            pc_col_name = self.key2col()[cn.CATEGORY_COL]
            return list(self.row_value_df[pc_col_name].unique())
        else:
            return []
    
    def get_standards(self, parameter)->list:
        casnr = self.parameter_map_df.loc[parameter]['casnr']
        result = []
        for guideline in self.guidelines:
            try:
                df = guideline['data']
                value = df.query('casnr == @casnr')
                if len(value) > 0:
                    result.append({'name': guideline['name'],
                                'value': value.iloc[0]['value'],
                                'unit': value.iloc[0]['unit']
                    })
            except:
                print('error occurred when retriebving the guideline list')
        return result

    def is_logged_in(self):
        return self.logged_in_user != None