qry = {
    'get_usr_pwd': "select password from public.user where email = '{}'",

    'user_info': "select * from public.user where email = '{}'",
    
    'change_pwd': "update public.user set password = '{}' where email = '{}'",

    'update_user': """Update public.user set first_name = '{}'
        , last_name = '{}'
        , company = '{}'
        , country = '{}'
        , language = '{}'
    where 
        email = '{}'
    """,
    
    'update_project': """UPDATE public.project
	SET title='{}', description='{}', row_is='{}', date_format='{}', separator='{}', encoding='{}', url_source='{}', is_public={}, has_separate_station_file={}
	WHERE id={};
    """,

    'insert_project': """INSERT INTO public.project(
	title, description, row_is, date_format, separator, encoding, url_source, is_public, owner_id)
	VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, {});
    """,

    'max_project_id': "select max(id) from public.project where owner_id = {}",
    
    'insert_user_project': "insert into public.user_project(user_id, project_id, role_id) values({},{},{})",
    
    'update_password': "Update public.user set password = '{}' where email = '{}'",

    'project': "Select * from public.project where id = {}",
    
    'public_projects': "Select * from public.project where is_public order by title",
    'user_projects': """select t1.* from public.project t1
        left join public.user_project t2 on t2.project_id = t1.id
        where t1.is_public
        or t2.user_id = {}
        order by title""",
    
    'station_data': """select {0}
	, to_char(min(t2.sampling_date), '{2}') as first_sample
	, to_char(max(sampling_date), '{2}') as last_sample
	, count(*) as number_of_samples
    from public.{1}_station t1 
    inner join (Select station_id, sampling_date from public.{1}_observation 
                    group by station_id,sampling_date) t2 on t2.station_id = t1.id
    group by {0}
    """,

    'station_samples': """select 
    {0}, count(*) as observations
    from public.{1}_observation t1 
    where 
        station_id = {2}
    group by 
        {0}
    order by 
        {0}
    """,
    
    'sample_observations': """
    select {0}
    from 
        public.{1}_observation t1
        inner join public.{1}_parameter t2 on t2.id = t1.parameter_id
    where 
        t1.sample_number = '{2}'
    """,

    'parameter_data': """select *
        from public.{}_parameter
        order by group1, parameter_name""",
    
    'parameter_observations':  """select {0}, t1.parameter_id, t1.station_id
        from 
            public.{1}_observation t1
            inner join public.{1}_station t2 on t2.id = t1.station_id
            inner join public.{1}_parameter t3 on t3.id = t1.parameter_id
        where 
            t1."parameter_id" = {2} {3}
        order by 
            t2."station_identifier", t1."sampling_date"
    """,
    
    'station_list': "select id, station_identifier from public.{}_station order by station_identifier",

    'min_max_sampling_date': "select min(sampling_date) as min_date, max(sampling_date) as max_date from public.{}_observation",
''
    'parameter_list': "select id, parameter_name from public.{}_parameter {} order by parameter_name",


    'observations': """Select {0}
        from public.{1}_observation t1
            inner join public.{1}_station t2 on t2.id = t1.station_id
            inner join public.{1}_parameter t3 on t3.id = t1.parameter_id
        where 1=1 {2}
    """,

    'get_analysis_config': "select * from public.user_project_config where user_id = {} and analysis_id = {} and setting_name='{}'",

    'update_analysis_config': "update public.user_project_config set config = '{}' where user_id = {} and analysis_id = {} and setting_name='{}'",

    'guidelines': "select id, title from public.guideline where is_active order by title",

    'guideline_detail': "select * from public.guideline where id = {}",

    'guideline_items': "select id, parameter, casnr, master_parameter_id, min_value, max_value, comments, unit from public.guideline_item where guideline_id = {}",

    'parameter_detail': """select t1.id,t1.parameter_name,t1.casnr,t1.master_parameter_id,t1.group1,t1.group2, t2.name_en as sys_name, t2.casnr as sys_casnr, 
            t2.formula as sys_formula, t2.fmw as sys_fmw, t2.valence as sys_valence, t2.unit_cat as sys_unit_cat, t2.unit as sys_unit
        from 
            public.{}_parameter t1
            left join public.master_parameter t2 on t2.id = t1.master_parameter_id
        where t1.id = {}""",
    
    'exceedance_list': """select t2.station_identifier
            , TO_CHAR(sampling_date :: DATE, 'dd/mm/yyyy') as sampling_date
            , t3.parameter_name
            , t1.unit
            , t1.value
            , t1.value_numeric
            , {0} as standard
            , case when t1.value_numeric > {0} then 'yes' else 'no' end as exceedance
        from
            public.{1}_observation t1
            inner join public.{1}_station t2 on t2.id = t1.station_id
            inner join public.{1}_parameter t3 on t3.id = t1.parameter_id
        where parameter_id = {2}""",
        
    'standard_parameter_list': "select id, parameter from public.guideline_item where guideline_id = {} order by parameter ",

    'sys_parameters': "select * from public.master_parameter",

    'project_parameters': """
        SELECT 
            t1.*, t2.name_en, t2.short_name_en, t2.formula, t2.formula_valence, t2.fmw, t2.valence, t2.unit_cat, t2.unit as default_unit 
        FROM 
            public.{}_parameter t1 
            left join public.master_parameter t2 on t2.id = t1.master_parameter_id""",

    'project_columns': """
        select * FROM  {}_column
        """,

    'date_list4station':"""select sampling_date as date, to_char(sampling_date, 'DD.MM.YYYY') as fmt_date from public.{}_observation
        where station_id = {}
        group by sampling_date
        order by sampling_date
    """,

    'station': """select * from public.{}_station where id = {}""",

    'station_fields_ordered': "select * from public.{}_parameter where parameter_type_id = 13 order by sort_id",

    'column_config': """
        select 
	        t1.column_name, t1.id, t1.master_parameter_id, t1.type_id, t1.data_type_id, t2.key as master_parameter_key
        from 
	        public.{}_column t1
	        left join public.master_parameter t2 on t2.id = t1.master_parameter_id""",

    'parameters_config': "select * from public.{}_parameter",

    'master_columns': "select * from public.master_parameter order by name_en",

    'lookup_values': "SELECT id, {0} as name FROM public.lookup_value where category_id = {1} order by {0}",

    'mandatory_parameters': "select id, name_{} as name from public.master_parameter where is_mandatory and type = '{}'",

    'update_parameter_id': """update public.{0}_temp t1 set "parameter_id" = t2."id"
        from 
            public.{0}_parameter t2
        where 
            t2."{1}" = t1."{2}";
        """,

    'update_station_id': """update public.{0}_temp t1 set "station_id" = t2."id"
        from 
            public.{0}_station t2
        where 
            t2."{1}" = t1."{2}";
        """,
    'truncate_table': """TRUNCATE TABLE public.{} RESTART IDENTITY;""",

    'update_num_value_col':"""
        update public.{0}_temp set "value_numeric" = "value" ::DECIMAL
        where isnumeric("value");

        update public.{0}_temp set "value_numeric" = (substring("value",2,char_length("value")) ::DECIMAL) / 2
        where substring("value",1,1)='<' and isnumeric(substring("value",2,char_length("value")));

        update public.{0}_temp set 
            "is_non_detect" = true,
            "detection_limit" = (substring("value",2,char_length("value")) ::DECIMAL)
        where substring("value",1,1)='<' and isnumeric(substring("value",2,char_length("value")));
    """,

    'parameter_group_list': """select distinct "group{0}" from public.{1}_parameter order by group{0}""",

    'proj_time_series': """select sampling_date, value, value_numeric, unit, station_id, parameter_id
        from public.{}_observation 
        where parameter_id = {} and station_id in ({})
        order by station_id, sampling_date""",
    
    'sample_list': """select t1.sampling_date, t1.sample_number, t2.station_identifier, count(*) as num_observations
        from public.{0}_observation t1
        inner join public.{0}_station t2 on t2.id = t1.station_id
        {1}
        group by t1.sampling_date, t1.sample_number, t2.station_identifier
    """,

    'phreeqc_observations': """select t1.sampling_date, t1.sample_number, t3.solution_master_species, t2.parameter_name, t1.value, t1.value_numeric, t1.unit, t1.station_id, t1.parameter_id
        from public.{0}_observation t1
        inner join public.{0}_parameter t2 on t2.id = t1.parameter_id
        inner join public.master_parameter t3 on t3.id = t2.master_parameter_id
        where t3.solution_master_species is not null and t1.sample_number = '{1}'
        order by station_id, sampling_date""",

    'sample_number_from_station_date': "select sample_number from public.{}_observation where station_id = {} and sampling_date = '{}' limit 1",

    'project_stations': "select * from public.{}_station order by station_identifier"
    
}
