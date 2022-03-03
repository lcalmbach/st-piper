update public.p0001_station set 
	longitude = cast(SPLIT_PART(geopoint::TEXT, ',', 1) as DECIMAL), 
	latitude = cast(SPLIT_PART(geopoint::TEXT, ',', 2) as DECIMAL);
	
update public.p0001_data t1 set station_id = t2.id
from 
p0001_station t2
where t2.identifier = t1.station_key;

update public.p0001_data t1 set parameter_id = t2.id
from 
p0001_parameters t2
where t2.parameter_key = t1.parameter;

update public.p0001_parameters t1 set group1 = gruppe, group2 = parameter_group
from 
(select distinct parameter_id, gruppe, parameter_group from p0001_data) t2
where t2.parameter_id = t1.id;

update public.p0001_data set 
	sampling_date = TO_DATE(probenahmedatum::TEXT,'DD.MM.YYYY');

update public.p0001_station t1 set depth = station_depth
from 
(select station_id, min(numeric_value) as station_depth
from public.p0001_data
where parameter = 'Sohlentiefe'
group by station_id) t2 
where t2.station_id = t1.id;

update public.p0001_parameters t1 set sys_par_id = t2.id
from 
public.meta_master_parameters t2
where t2.key = t1.key;

update public.p0001_data set numeric_value = cast(right(value,length(value)-1) as decimal) / 2
where left(value,1)='<'

insert into public.user_project_config (user_id, analysis_id, config, setting_name)
select -1,analysis_id,config,setting_name from public.user_project_config where user_id = 2

insert into public.user_project_config(user_id,analysis_id,setting_name,config)
select 2,id,'default',default_config
from public.analysis
where id not in (select analysis_id from public.user_project_config where user_id = 2)

update public.p0001_parameter t1 set unit = t2.unit 
from 
	(select parameter, parameter_id, unit from public.p0001_data group by parameter, parameter_id, unit  order by parameter) t2
	where t2.parameter_id = t1.id;