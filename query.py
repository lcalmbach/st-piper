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
	SET title='{}', description='{}', row_is='{}', date_format='{}', separator='{}', encoding='{}', url_source='{}', is_public={}
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
    
    'station_data':"""select 
	t1.id
	, t1.identifier
	, t1.longitude
	, t1.latitude
	, t1.elevation
	, t1.depth
	, min(t2.sampling_date) as date_from
	, max(sampling_date) as date_to
	, count(*) as no_of_samples
from public.{0}_station t1 
inner join (Select station_id,sampling_date from public.{0}_data group by station_id,sampling_date) t2 on t2.station_id = t1.id
group by t1.id, t1.identifier, t1.longitude, t1.latitude, t1.elevation, t1.depth
order by t1.identifier
    """,

    'station_samples': """select 
    station_key, sampling_date, count(*) as observations
    from public.{0}_data t1 
    where 
        station_id = {1}
    group by 
        station_key,sampling_date
    order by 
        station_key,sampling_date
    """,
    
    'sample_observations': """
    select 
        sampling_date
        ,parameter
        ,casnr
        ,unit
        ,value
        ,numeric_value
        ,detect_limit
        ,group1
        ,group2
    from 
        public.{0}_data t1
        inner join public.{0}_parameter t2 on t2.id = t1.parameter_id
    where 
        station_id = {1} and sampling_date = '{2}'
    """,

    'parameter_data': """select id, parameter_name, casnr, group1, group2
        from public.{}_parameter
        order by group1, group2""",
    
    'parameter_observations': """select * from public.{}_data where parameter_id = {} 
{} 
order by station_key, sampling_date""",

    'station_list': "select id, identifier from public.{}_station order by identifier",

    'min_max_sampling_date': "select min(sampling_date) as min_date, max(sampling_date) as max_date from public.{}_data",

    'parameter_list': "select id, parameter_name from public.{}_parameter {} order by parameter_name",

    'observations': "select * from public.{}_data where 1=1 {}",

    'get_analysis_config': "select * from public.user_project_config where user_id = {} and analysis_id = {} and setting_name='{}'",

    'update_analysis_config': "update public.user_project_config set config = '{}' where user_id = {} and analysis_id = {} and setting_name='{}'",

    'guidelines': "select id, title from public.guideline where is_active order by title",

    'guideline_detail': "select * from public.guideline where id = {}",

    'guideline_items': "select id, parameter, casnr, sys_par_id, min_value, max_value, comments, unit from public.guideline_item where guideline_id = {}",

    'parameter_detail': """select t1.id,t1.parameter_name,t1.casnr,t1.sys_par_id,t1.group1,t1.group2, t2.name_en as sys_name, t2.casnr as sys_casnr, 
            t2.formula as sys_formula, t2.fmw as sys_fmw, t2.valence as sys_valence, t2.unit_cat as sys_unit_cat, t2.unit as sys_unit
        from 
            public.{}_parameter t1
            left join public.meta_master_parameter t2 on t2.id = t1.sys_par_id
        where t1.id = {}""",
    
    'exceedance_list': """select t2.identifier as station, TO_CHAR(sampling_date :: DATE, 'dd/mm/yyyy') as sampling_date, t3.parameter_name, t1.unit, t1.value, 
            t1.numeric_value, {0} as standard, case when t1.numeric_value > {0} then 'yes' else 'no' end as exceedance
        from
            public.{1}_data t1
            inner join public.{1}_station t2 on t2.id = t1.station_id
            inner join public.{1}_parameter t3 on t3.id = t1.parameter_id
        where parameter_id = {2}""",
        
    'standard_parameter_list': "select id, parameter from public.guideline_item where guideline_id = {} order by parameter ",

    'sys_parameters': "select * from public.meta_master_parameter",

    'project_parameters': """
        SELECT 
            t1.*, t2.name_en, t2.short_name_en, t2.formula, t2.formula_valence, t2.fmw, t2.valence, t2.unit_cat, t2.unit as default_unit 
        FROM 
            public.{}_parameter t1 
            left join public.meta_master_parameter t2 on t2.id = t1.id"""
}