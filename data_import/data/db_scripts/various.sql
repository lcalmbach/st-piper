-- generate dict for master parameters.ABORT
select '''' || key || ''': ' || TO_CHAR(id,'99') ||',' from public.master_parameter where type_id = 13

select key || ' = ' || trim(to_char(id,'99')) from public.master_parameter