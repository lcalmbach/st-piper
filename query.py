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
    'user_projects': """select * from public.project t1
        left join public.user_project t2 on t2.project_id = t1.id
        where t1.is_public
        or t2.user_id = {}
        order by title"""

}