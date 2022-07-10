import os
import socket

DEV_MACHINES = ('liestal')
if socket.gethostname().lower() in DEV_MACHINES:
    DB_USER = "postgres"
    DB_PASS = 'password'
    DB_HOST = 'localhost' 
    DB_DATABASE = 'fontus'
    DB_PORT = "5432"
else:
    DB_USER = os.environ.get('DB_USER') # read from system variables when on heroku
    DB_PASS = os.environ.get('DB_PASS') 
    DB_HOST = os.environ.get('DB_HOST') 
    DB_DATABASE = os.environ.get('DB_NAME') 
    DB_PORT = "5432" 