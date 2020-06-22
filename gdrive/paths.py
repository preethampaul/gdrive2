
import os

VERSION = '0.6.2'
#Deafult info during initialization
DEFAULT_INFO = {
        'default_parent' : 'origin',
        'origin' : ['no_user', '', 'root', 'My Drive', 'root', 'client_secrets']
        #parent_name : [user_name, parent_path, parent_id, drive_name, drive_id, <name of client secrets json>]
        }

#Folder names
API_DATA_FOLDER = 'api_data'
CRED_MAP = 'creds'
CLIENT_FOLDER = 'client_secrets'

#Credentials and util paths
ROOT_PATH = os.path.dirname(__file__)
CREDS_DIR = os.path.join(ROOT_PATH, API_DATA_FOLDER)

#Credentials
CRED_MAP_PATH = os.path.join(CREDS_DIR, CRED_MAP)

#Default client secrets json name
DEFAULT_CLIENT = DEFAULT_INFO[DEFAULT_INFO['default_parent']][5]
CLIENT_SECRETS_DIR = os.path.join(CREDS_DIR, CLIENT_FOLDER)

if not os.path.exists(CREDS_DIR):
    os.mkdir(CREDS_DIR)
if not os.path.exists(CLIENT_SECRETS_DIR):
    os.mkdir(CLIENT_SECRETS_DIR)
