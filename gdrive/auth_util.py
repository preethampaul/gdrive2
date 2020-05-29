#This file contains functions relevant to authentication of parents
#and handling of credential and client files

import os
import uuid
import json
import shutil

#paths.py contains all the credential path information
if __name__ == 'auth_util':
    from paths import *
else:
    from .paths import *

def check_creds_list(user_name, check_only=False):
    """
    checks if creds list (CRED_MAP) exists and creates one if it doesn't
    looks for username in the CRED_MAP, if it doesnt exist
    creates unique id for the username and generates a credentials file for it.

    Parameters
    -----------
    user_name : string
        username to check
    check_only : boolean (optional)
        If True, returns a boolean value stating whether the username is previously registered or not.
    
    Returns
    -----------
    whether username exists already : boolean
        if check_only = True
    cred_id : string
        the credentials file's unique id if check_only = False
    """


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


def copy_client_secrets(client_path, client=None):
    """
    Copies client secrets .json files from client_path to the client_secrets/
    in the package folder

    Parameters
    ------------
    client_path : string
        path to look for the source .json file
    client : string (optional)
        Name to be assigned to the client file. If None, DEFAULT_CLIENT name is assigned.
        Note that client should not include the extension '.json' in it
    .
    Returns
    ------------
    None
        Just copies the .json file

    """
    
    if not os.path.exists(client_path):
        raise Exception("The path: '" + client_path + "' doesn't exist.")
    
    #Using default client name
    if client==None:
        client_file = DEFAULT_CLIENT +'.json'
    #Using client name provided
    else:
        client_file = client +'.json'
   
    dest_path = os.path.join(CLIENT_SECRETS_DIR, client_file)    
    shutil.copyfile(client_path, dest_path)
    print(client_file+ " created.")


def auth_from_cred(gauth, user_name=None, client=DEFAULT_CLIENT):
    """
    Stores the authentication information in the gauth object
    Also required to retrieve credential data and refresh expired access tokens
    Checks for <cred_id>.txt and client_secrets/<client>.json paths
    Also, updates these paths with authentication
    
    Parameters
    --------------
    gauth : pydrive.GoogleAuth() object
    user_name : string (optional)
        the username which requires authentication
    client : string (optional)
        client <name> corresponding to <name>.json in client_secrets/ folder
        If no client is passed, the DEFAULT_CLIENT is used.

    Returns
    --------------
    None
        Authenticates the username with the client provided

    """
    
    if user_name==None:
        user_name = 'no_user'
    
    #Checking client_secrets
    CLIENT_FILE = client +'.json'
    CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)
    
    if len(CLIENT_SECRETS_LIST)==0:
        print("No client secret files available.")
        client_path = input("Enter absolute path to a client_secrets file on system: ")
        copy_client_secrets(client_path)
        CLIENT_FILE = DEFAULT_CLIENT + '.json'
        
    else:    
        if CLIENT_FILE in CLIENT_SECRETS_LIST:
            CLIENT_SECRETS_PATH = os.path.join(CLIENT_SECRETS_DIR, CLIENT_FILE)
        else:
            print(CLIENT_FILE + " not found in "+ CLIENT_SECRETS_DIR)
            prompt = input("Do you want to register the new client secrets file? [y/n]: ")
            if prompt=='y':
                client_path = input("Enter absolute path to the " + CLIENT_FILE + " file on system: ")
                copy_client_secrets(client_path, client)
            elif prompt=='n':
                raise Exception(CLIENT_FILE + " not found in "+ CLIENT_SECRETS_DIR + ". Try another client.")
            else:
                raise Exception("Invalid arguement passed.")
    
    CLIENT_SECRETS_PATH = os.path.join(CLIENT_SECRETS_DIR, CLIENT_FILE)            
    
    #creating creds_path
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
                print('Refresh token Expired : authentication required ...')
                gauth.LocalWebserverAuth()
                
        else:
            # Initialize the saved creds
            gauth.Authorize()
        
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(creds_path)
    
    else:
        if not os.path.exists(CLIENT_SECRETS_PATH):
            print("client secrets file not found. Download and paste it in : " + CLIENT_SECRETS_DIR)
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
                
