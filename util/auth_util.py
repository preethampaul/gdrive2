import os
import uuid
import json

UTIL_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(UTIL_PATH)
CLIENT_SECRETS = 'client_secrets.json'
CRED_MAP = 'creds'
CREDS_DIR = os.path.join(ROOT_PATH, 'api_data')

CRED_MAP_PATH = os.path.join(CREDS_DIR, CRED_MAP)
CLIENT_SECRETS_PATH = os.path.join(CREDS_DIR, CLIENT_SECRETS)
#gauth must be a GoogleAuth() object

def check_creds_list(user_name, check_only=False):
    
    if os.path.exists(CRED_MAP_PATH):
        with open(CRED_MAP_PATH, 'r') as file:
            creds_list = file.read().split(' ')
        
        try:
            cred_index = creds_list.index(user_name)
            
            if check_only:
                return True
                
            return creds_list[cred_index + 1]
            
        except:
            
            if check_only:
                return False
            
            cred_id = str(uuid.uuid1())
            with open(CRED_MAP_PATH, 'a') as file:
                file.write(' '+ user_name +' ' + cred_id)
                
            return cred_id
        
    else:
        
        if check_only:
            return False
            
        cred_id = str(uuid.uuid1())
        with open(CRED_MAP_PATH, 'w') as file:
            file.write(' '+ user_name +' ' + cred_id)
            return cred_id
        

def auth_from_cred(gauth, user_name=None):
    """
    This function stores the authentication information
    in the gauth object
    Also required to retrieve credential data from creds_path
    and refresh expired access tokens
    
    Checks for <cred_id>.txt and client_secrets.json paths
    Also, updates these paths with authentication
    
    Input : gauth = pydrive.GoogleAuth() object
    """
    
    if user_name==None:
        user_name = 'no_user'
    
    #creating for creds_path
    creds_id = check_creds_list(user_name)
    creds_path = os.path.join(CREDS_DIR, creds_id)
        
    if os.path.exists(creds_path) and os.path.exists(CLIENT_SECRETS_PATH):
        
        # Try to load saved client credentials
        gauth.LoadCredentialsFile(creds_path)
        gauth.LoadClientConfigFile(CLIENT_SECRETS_PATH)
        
        if gauth.credentials is None:
            # Authenticate if they're not there
            print('Credentials empty : authentication required ...')
            gauth.LocalWebserverAuth()
        
        elif gauth.access_token_expired:
            # Refresh them if expired
            try:
                gauth.Refresh()
            except:
                print('username : ' + user_name)
                print('Token Expired : authentication required ...')
                gauth.LocalWebserverAuth()
                
        else:
            # Initialize the saved creds
            gauth.Authorize()
        
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(creds_path)
    
    else:
        if not os.path.exists(CLIENT_SECRETS_PATH):
            print("client secrets file not found. Download and paste it in : " + os.path.join(ROOT_PATH, 'api_data'))
            return
        
        else:
            try:
                
                print("\n----------Authentication required-----------\n")
                with open(CLIENT_SECRETS_PATH) as file:
                    temp = json.load(file)
                    
                gauth.LoadClientConfigFile(CLIENT_SECRETS_PATH)
                gauth.LocalWebserverAuth()
                gauth.SaveCredentialsFile(creds_path)
            
            except:
                print("client secrets file found in '"+ CLIENT_SECRETS_PATH + "' is invalid.")
                
