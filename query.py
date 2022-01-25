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
    """
}