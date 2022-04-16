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
	(select parameter, parameter_id, unit from public.p0001_data group by parameter, parameter_id, unit) t2
	where t2.parameter_id = t1.id;

--bgs dataset
update public.temp_data t1 set station_id = t2.id
from 
	p0002_station t2
where t2."STATION_ID" = t1."STATION_ID";

truncate table public.p0002_data;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'As', 1, "As", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "As" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Al', 1, "Al", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Al" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'B', 3, "B_", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "B_" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Ba', 4, "Ba", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Ba" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Ca', 5, "Ca", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Ca" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Co', 6, "Co", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Co" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Cr', 7, "Cr", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Cr" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Cu', 8, "Cu", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Cu" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Fe', 9, "Fe", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Fe" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'K_', 10, "K_", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "K_" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Li', 11, "Li", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Li" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Mg', 12, "Mg", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Mg" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Mn', 13, "Mn", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Mn" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Na', 14, "Na", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Na" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'P_', 15, "P_", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "P_" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Si', 16, "Si", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Si" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'SO4', 17, "SO4", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "SO4" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Sr', 18, "Sr", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Sr" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'V_', 19, "V_", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "V_" is not null;

insert into public.p0002_data(station_key,station_id,parameter,parameter_id, value, sample_number, sampling_date)
select "STATION_ID", station_id, 'Zn', 20, "Zn", "SAMPLE_FIELD_ID", to_date("SAMPLE_DATE",'DD/MM/YYYY')
from public.temp_data where "Zn" is not null;

UPDATE public.p0002_data SET numeric_value = value::float where isnumeric(value);

update public.p0002_data set numeric_value = cast(right(value,length(value)-1) as decimal) / 2
where left(value,1)='<';

update public.p0002_parameter t3 set sys_par_id = t2.id
from 
	public.p0002_parameter t1
	inner join public.meta_master_parameter t2 on t2.formula = t1.parameter_name
where t3.id = t2.id