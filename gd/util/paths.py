# -*- coding: utf-8 -*-
"""
Created on Sat May 23 19:02:32 2020

@author: Preetham
"""
import os

#Deafult info during initialization
DEFAULT_INFO = {
        'default_parent' : 'origin',
        'origin' : ['no_user', '', 'root', 'My Drive', 'root', 'client_secrets']
        #parent_name : [user_name, parent_path, parent_id, drive_name, drive_id, <name of client secrets json>]
        }

#Folder names
CRED_MAP = 'creds'
API_DATA_FOLDER = 'api_data'
CLIENT_FOLDER = 'client_secrets'

#Credentials and util paths
UTIL_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(UTIL_PATH)
CREDS_DIR = os.path.join(ROOT_PATH, API_DATA_FOLDER)

#Credentials
CRED_MAP_PATH = os.path.join(CREDS_DIR, CRED_MAP)

#Default client secrets json name
DEFAULT_CLIENT = DEFAULT_INFO['default_parent'][5]
CLIENT_SECRETS_DIR = os.path.join(CREDS_DIR, CLIENT_FOLDER)
CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)

if not os.path.exists(CREDS_DIR):
    os.mkdir(CREDS_DIR)
if not os.path.exists(CLIENT_SECRETS_DIR):
    os.mkdir(CLIENT_SECRETS_DIR)