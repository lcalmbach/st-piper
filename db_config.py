import os
import socket

# database settings on heroku
DEV_MACHINES = ('liestal')
if socket.gethostname().lower() in DEV_MACHINES:
    DB_USER = "postgres"
    DB_PASS = 'password'
    DB_HOST = 'localhost' 
    DB_DATABASE = 'fontus'
    DB_PORT = "5432"
else:
    DB_USER = "dxkqwxlfbaffnk"
    DB_PASS = os.environ.get('DB_PASS') # read from system variables when on heroku
    DB_HOST = 'ec2-54-216-17-9.eu-west-1.compute.amazonaws.com'
    DB_DATABASE = 'd3f49ft1g3uc8t'
    DB_PORT = "5432"