#!/usr/bin/env python

import argparse
import os
import json
import re
import shutil

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

if __name__ == "__main__":
    from paths import *
    from auth_util import *
    from drive_util import *
else:
    from .paths import *
    from .auth_util import *
    from .drive_util import *
    
#Important objects for gdrive
gauth = GoogleAuth()    #for authentication
drive = GoogleDrive(gauth) #for drive utilities

#set to True when importing gd.py
RETURN_RESULT = False

#Current Working Directory
CURR_PATH = os.getcwd()
#Local Home directory
CURR_HOME_DIR = '/'.join(re.split('[\\\\/]', os.path.expanduser('~')))
#Main Home directory
HOME_DIR = re.split("[\\\\/]", CURR_PATH)[0]

#Info paths in current directory
INFO_FOLDER = os.path.join(CURR_PATH,'.gd')
INFO_PATH = os.path.join(INFO_FOLDER, '.gdinfo.json')
STAGE_PATH = os.path.join(INFO_FOLDER, '.gdstage')

#Text to show for 'gd -help'
help_text = "\n\
<func> = function name\n\
<args> = arguements\n\n\
Overview of initializing/listing fucnctions:\n\
--------------------------------\n\
'init'   : initialize gdrive, add new parents to initialized dir., add new clients\n\
'status' : show parents list, show stage list, show users and clients list\n\
'reset'  : changes default parent, client secrets\n\
           changes parent information like user_names, paths, root folders (Ex: shared drives), clients\n\
           deletes parents, delete authentication data,\n\
'ls'     : lists all files/folders in parent paths, shows registered usernames and their shared drives, clients\n\
'find'   : Searches for files and folders based on query\n\
'cd'     : changes parent_path directly without using 'reset' function\n\
'mkdir'  : creates new folder in the parent or path provided\n\
'rm'     : creates existing folder/file in the parent or path provided\n\
\n\
Overview of push/pull functions:\n\
---------------------------------\n\
'add'    : adds paths to the stage, clear stage\n\
'push'   : uploads files/folders to parent_paths\n\
'pull'   : downloads files/folders from parent_paths\n\n\
\n\
Miscelleneous functions:\n\
---------------------------------\n\
'help'   : Shows the list of functions or commands available\n\
'rmgd'   : Removes the gd file created by importing gdrive\n\
'default' : Brings the package to its default state (removes all clients, auth. data and the gd commandline functionality)\n\
\n\
Use '-h' / -h  or '-help' / -help to see help about a function/command.\n\
Example: gdrive.init(['-h']) / gd init -h\n"

#---------------------------------------------------------------------------------------
#UTILITY-FUNCTIONS
#These are used in main command functions
#---------------------------------------------------------------------------------------


def check_user_name(user_name=None):
    """ Checks if username is valid/ already assigned """

    if user_name == None:
        print("The username you set will represent the Google account.")
        user_name = input('username for drive acc. : ')
        check_only = False
    else:
        check_only = True
    
    #check_only validates only if given user_name is already registered or not
    #WITHOUT asking for prompts
    exists_bool = False
    prob = True
    
    while prob:
        
        prob = False
        if ' ' in user_name:
            if check_only:
                break
            user_name = input('Enter without space : ')
            prob = True
        
        if user_name == 'default':
            if os.path.exists(INFO_PATH):
                with open(INFO_PATH, 'r') as file:
                    info = json.load(file)
                
                user_name = info[info['default_parent']][0]
                prob = False
                exists_bool = True
                print("default user_name : " + user_name)
                
            else:
                if check_only:
                    break
                user_name = input("<default> user_name not yet created; try another user_name : ")
                prob = True
                
    
        if check_creds_list(user_name, check_only=True):
            print('This account already registered.')
            prob = False
            exists_bool = True
            
        if len(user_name)<6 or len(user_name)>15:
            if check_only:
                break
            user_name = input('Enter only 6-15 no. of characters : ')
            prob = True
    
    if not exists_bool:
        if not check_only:
            print('New gdrive account registered.')
    
    return user_name, exists_bool

#-----------------------------------------
def check_info():
    """Checks if the info file exists in current working directory"""
    
    info = {}
    
    if os.path.exists(INFO_PATH):
        with open(INFO_PATH) as file:
            info = json.load(file)
            
    return info
    
#------------------------------------------
def create_info(info, parent_path=DEFAULT_INFO[DEFAULT_INFO['default_parent']][1],
                parent_name=DEFAULT_INFO['default_parent'],
                drive_name=DEFAULT_INFO[DEFAULT_INFO['default_parent']][3],
                drive_id=DEFAULT_INFO[DEFAULT_INFO['default_parent']][4],
                same_user=False):

    """Creates a new info file"""
    
    if len(info) == 0:
        #default values
        create_folders_path(INFO_FOLDER)
        with open(STAGE_PATH, 'w') as file:
            pass
        
        info = DEFAULT_INFO
    
    else:
        if not parent_name in list(info.keys()):
            def_parent = info['default_parent']
            info[parent_name] = [info[def_parent][0], parent_path, *DEFAULT_INFO[DEFAULT_INFO["default_parent"]][2:]]
            
        info[parent_name][1] = parent_path
        info[parent_name][3] = drive_name
        info[parent_name][4] = drive_id
    
    if not same_user:
        info[parent_name][0], _ = check_user_name()
        
    auth_from_cred(gauth, info[parent_name][0], info[parent_name][5])
    drive = GoogleDrive(gauth)
    info[parent_name][2] = get_path_ids(parent_path, drive, create_missing_folders = False, path_to = 'folder', default_root=drive_id)[-1]
    
    with open(INFO_PATH, 'w') as file:
        json.dump(info, file)

#---------------------------------------------
def check_parent_name():
    """Checks if the parent name input is valid/ already exists within the current directory"""
    
    with open(INFO_PATH, 'r') as file:
        info = json.load(file)
        
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    
    par = input('Enter new parent name : ')
    
    prob = True
    
    while prob:
        
        prob = False
        if ' ' in par or '-' in par:
            par = input("Enter without space or '-': ")
            prob = True
    
        if par in parent_list:
            par = input('This name already exists. Enter another :')
            prob = True
            
        if par == 'default_parent':
            par = input('This name is not allowed. Try another:')
            prob = True
            
    return par

#--------------------------------------------
def check_client(client=None):
    """Asks for input and checks if the client"""
    
    #List of client files
    CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)
    
    #When client is not passed as arguement
    if client==None:
        clients_list = [re.split('.json', i)[0] for i in CLIENT_SECRETS_LIST]
        print("\nClient secrets file names available :\n----------------------")
        for i in range(len(clients_list)):
            print(str(i+1) + ". " + clients_list[i])
        
        print('')
        client_num = -1
        while not (client_num>0 and client_num <=len(clients_list)):
            client_num = input("Enter the sr. no. of client name from list above: ")
            try:
                client_num = int(client_num)
            except:
                client_num = -1
            
        client = clients_list[client_num-1]
        client_exists = True
        
    else:
        CLIENT_FILE = client +'.json'
        client_exists = CLIENT_FILE in CLIENT_SECRETS_LIST
    
    return client, client_exists

#--------------------------------------------
def delete_cred_files():
    """Deletes all the authentication data except cred_map and client_secrets"""
    file_list = os.listdir(CREDS_DIR)
    file_list.remove(CLIENT_SECRETS_DIR)
    file_list.remove(CRED_MAP)
    
    for i in file_list:
        os.remove(os.path.join(CREDS_DIR, i))

#---------------------------------------------------------------------------------------------------
#USAGE-FUNCTIONS:
#These are the main command functions called from terminal
#---------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
# 1. FIlE-VIEWING & INFO-MANAGING FUNCTIONS       
# The first set of functions are used to manage files within Google drive and to edit the
# info file in the cwd of local system.
#--------------------------------------------------------------------------------------------
        
def init(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Initializes the current working directory and
    Creates an info file and authenticates the username.
    
    If used for the first time, the username and authentication are requested.
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Just creates the .gd folder
    

    Notes
    ----------
    The following commands go into args :
        
    '-h' / -h  or '-help' / -help : shows help
    
    '-add' / -add                 : adds new parent to the current directory

    '--add-client' / --add-client : registers new client secrets file.
    

    Examples
    ----------
    init([])       / gd init
    
    init(['-add']) / gd init -add
    
    """

    if '-h' in args or '-help' in args:
        print(init.__doc__)
        return
    
    info = check_info()
    parent_name = DEFAULT_INFO['default_parent']
    
    if '-add' in args:
        parent_name = check_parent_name()
        create_info(info, parent_name=parent_name, same_user=False)
        print(parent_name + " : new parent created.")
        return
    
    if '--add-client' in args:
        #List of client files
        CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)
        
        client_path = input("Enter absolute path to the new client secrets file: ")
        client = input("Enter new client <name> as in <name>.json with no spaces : ")
        
        valid_client = False
        
        while not valid_client:
            
            if '.' in client:
                client = input("Enter client's name without file extension:")
                continue
            
            if client + '.json' in CLIENT_SECRETS_LIST:
                print("Client name: " + client + " already exists.")
                client = input("Choose another name: ")
                continue
                
            valid_client = True
            
        copy_client_secrets(client_path, client)
        return
        
    if not len(args) == 0:
        print("Command unknown.")
        print("Expected commands : gd init [-add]")
        return
    
    if len(info)==0:
        
        if not len(args)==0:
            print('gdrive not initialized in this folder. Try command : gd init')
            return
        
        create_info(info)
    
    else:
        auth_from_cred(gauth, info[parent_name][0], info[parent_name][5])


#------------------------------------------
def reset(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Modifies/deletes the parent information of the current working directory.
    Deletes authentication data in the local system
    Resets the current working directory
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    returns
    ----------
    None
        Just modifies or deletes the info file or the credentials.
    

    Notes
    ----------
    The following commands go into args :
            
    0. '-h' / -h  or '-help' / -help : shows help

    1. reset(['<parent_name>', ]) / gd reset <parent_name>
        If no arg. after '<parent_name>', it prompts inputs for
        user_name, path and default prop. of existing parent
        
        optional arguements after '<parent_name>' / <parent_name>:
            
        '-user' / -user   : resets user_name/account in the parent name given.

        '-path' / -path   : resets path in the parent name given.
        
        '-drive'/ -drive  : resets drive in the parent name given (useful to set shared drives as roots)
        
        '-d'    / -d      : deletes parent name given and its path, user_name and id
        
        '-default' / -default : set parent name given as 'default'
        
        '-client' / -client : resets the client secrets file name for the parent.
    
    2. reset(['-info']) / gd reset -info
        erases all parents and user_names for current directory and re-initializes
    
    3. reset(['-user', ]) / gd reset -user
        required arguements after '-user' / -user :
        
        '<user_name>' / <user_name> : deletes <user_name>'s authentication data in the SYSTEM
        
        '-a'          / -a          : deletes all users authentication data in the SYSTEM
        
    4. reset(['-client', ]) / gd reset -client
        required arguements after '-client' / -client :
        
        '<client_name>' / <client_name> : deletes <client_name>.json
        
        '-a'          / -a              : deletes all client secrets files
        
    
    Examples
    ----------
    reset(['origin', '-path'])       / gd reset origin -path

    reset(['-info'])                 / gd reset -info
    
    reset(['-user', '<user_name>'])  / gd reset -user <user_name>
    
    """
    
    if '-h' in args or '-help' in args:
        print(reset.__doc__)
        return
    
    
    info = check_info()
    
    if not ('-user' in args or '-client' in args): 
        
        if len(info)==0:
            print('gdrive not initialized in this folder. Try command : gd init')
            return
    
        parents_list = list(info.keys())
        parents_list.remove('default_parent')
    
    if len(args)==0:
        print("More arguements expected like these: ")
        print("gd reset <parent_name> [-user, -path, -d, -default]")
        print("gd reset -info")
        print("gd reset -user [<user_name>, -a]")
        print("use 'gd reset -h' for help.")
        return
        
    else:
        parent_name = args[0]
        
        if parent_name == '-user':
            
            if not os.path.exists(CRED_MAP_PATH):
                print("No gdrive credentials found on this system.")
                return
                
            if len(args) == 2:
                user_name = args[1]
                user_name, exists_bool = check_user_name(user_name)
                
                if user_name == '-a':
                    prompt = input("This removes 'all' authentication data of gdrive accounts stored in this system. Continue? [y/n]")
                    if prompt=='y':
                        file_list = os.listdir(CREDS_DIR)
                        file_list.remove(CLIENT_FOLDER)
                        
                        for i in file_list:
                            os.remove(os.path.join(CREDS_DIR, i))
                        
                        if os.path.exists(INFO_PATH):
                            shutil.rmtree(INFO_FOLDER)
                            print("All authentication data deleted. Use `gd init` to re-initialize.")
                        
                        return
                    
                elif exists_bool:
                    with open(CRED_MAP_PATH, 'r') as file:
                        creds_list = file.read().split(' ')
                    
                    cred_id = creds_list[creds_list.index(user_name) + 1]
                    cred_path = os.path.join(CREDS_DIR, cred_id)
                    if os.path.exists(cred_path):
                        os.remove(cred_path)
                        
                    creds_list.remove(user_name)
                    creds_list.remove(cred_id)
                    
                    with open(CRED_MAP_PATH, 'w') as file:
                        file.write(' '.join(creds_list))
                        
                    return
                        
                else:
                    invalid_pars = []
                    for par in parents_list:
                        if user_name in info[par][0]:
                            invalid_pars.append(par)
                    
                    if len(invalid_pars)==0:
                        print("invalid username : " + user_name)
                    else:
                        print("user_name : '" + user_name + "' is already removed from system")
                        print("Delete [gd reset <parent_name> -d] or reset user_names [gd reset <parent_name> -user] for these parents :")
                        print(invalid_pars)
                    
                    return

            else:
                print("Unexpected/invalid no. of arguements passed. Use 'gd reset -h' for help.")
                return
        
        if parent_name == '-client':
            CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)
            if len(CLIENT_SECRETS_LIST) == 0:
                print("No client secret files found.")
                return
            
            if not len(args)==2:
                print("Invalid no. of arguements passed. Use 'gd reset -h' for help.")
                return
            
            client = args[1]
            client_file = client+'.json'
            
            if client == '-a':
                shutil.rmtree(CLIENT_SECRETS_DIR)
                os.mkdir(CLIENT_SECRETS_DIR)
                return
            
            if '.' in client:
                print("file extension should not be included in client name")
                return
            
            if client_file in CLIENT_SECRETS_LIST:
                os.remove(os.path.join(CLIENT_SECRETS_DIR, client_file))
                print(client_file + " removed from " + CLIENT_SECRETS_DIR)
                return
            else:
                print(client_file + " doesn't exist.")
                return
        
        #arguement is not a parent name
        if not parent_name in parents_list:
            if parent_name[0] != '-':
                print("'" + parent_name + "' : parent name not defined before.")
                print("try 'gd status' to get list of defined parent names.")
                print("try 'gd init -add' to add new parent")
                return
            else:
                if parent_name == '-info':
                    if len(args)>1:
                        print("Unexpected arguements passed. Use 'gd reset -h' for help.")
                        return
                    
                    shutil.rmtree(INFO_FOLDER)
                    print("Current directory reset.")
                    return
                
                else:
                    print("Unknown arguements passed. Use 'gd reset -h' for help.")
                    return
                                      
        #arguement is a parent name        
        else:
            user_name, exists_bool = check_user_name(info[parent_name][0])
                
            if len(args)==2:
                
                if args[1] == '-user':
                    create_info(info, parent_name=parent_name)
                    return
                    
                elif args[1] == '-path':
                    if not exists_bool:
                        print("user_name for this parent is deleted from the system.")
                        print("------")
                        print("Possible soultions :")
                        print("+ Delete this parent : 'gd reset "+ parent_name + " -d'")
                        print("+ Reset the user for this parent : 'gd reset " + parent_name + " -user'")
                        return
                    
                    print('Example folder path : folder_in_root/subfolder1/subfolder2')
                    parent_path = input("Enter drive folder path : ")
                    if "'" in parent_path or "\"" in parent_path:
                        parent_path = parent_path[1:-1]
                    
                    drive_name = info[parent_name][3]
                    drive_id = info[parent_name][4]
                    
                    create_info(info, parent_path, parent_name=parent_name, drive_name=drive_name, drive_id=drive_id, same_user=True)
                    print("\n" + parent_name + "'s path changed. Use 'gd status' to check.")
                    return
                
                elif args[1] == '-drive':
                    if not exists_bool:
                        print("The username : '" + user_name + "'is not registered. Add a new parent using 'gd init -add' to register username.")
                        print("Use 'gd reset' to change username or delete this parent.")
                        return
            
                    auth_from_cred(gauth, user_name, info[parent_name][5])
                    drives_list = gauth.service.drives().list().execute()['items']
                    drive_names_list = [dic['name'] for dic in drives_list]
                    drive_ids_list = [dic['id'] for dic in drives_list]
                    
                    print("Shared drives for username:" + user_name)
                    print("----------------------------------------")
                    for num in range(len(drive_names_list)):
                        print(str(num+1) + ". " + drive_names_list[num])
                    
                    print("----------------------------------------")
                    
                    drive_num = input("\nEnter serial no. of these shared folders : ")
                    try:
                        drive_num = int(drive_num)
                    except:
                        drive_num = -1
                    
                    while not (drive_num < len(drive_names_list)+1 and drive_num>0):
                        drive_num = input("\nPlease a serial number from list shown above: ")
                        try:
                            drive_num = int(drive_num)
                        except:
                            drive_num = -1
                    
                    drive_id = drive_ids_list[drive_num-1]
                    drive_name = drive_names_list[drive_num-1]
                    info[parent_name][2] = drive_id
                    info[parent_name][3] = drive_name
                    info[parent_name][4] = drive_id
                    
                    with open(INFO_PATH, 'w') as file:
                        json.dump(info, file)
                    
                    print(parent_name+": changed root drive to '"+drive_name+"'")
                        
                elif args[1] == '-default':
                    prev_def = info['default_parent']
                    info['default_parent'] = parent_name
                    if parent_name == prev_def:
                        print("'" + parent_name +"' is already the default parent.")
                    else:
                        with open(INFO_PATH, 'w') as file:
                            json.dump(info, file)
                        print("Default changed from '" + prev_def + "' to '" + parent_name +"'.")
                    
                    return
                
                elif args[1] == '-d':
                    par_def = info['default_parent']
                    if parent_name == par_def:
                        print("'" + parent_name + "'is the default parent : cannot delete a default parent.")
                        print("Try changing another parent to default with : 'gd reset <parent_name> -default'")
                        return
                    else:
                        del info[parent_name]
                        with open(INFO_PATH, 'w') as file:
                            json.dump(info, file)
                        print(parent_name + " deleted.")
                        return
                
                elif args[1] == '-client':
                    client,_ = check_client()
                    info[parent_name][5] = client
                    with open(INFO_PATH, 'w') as file:
                        json.dump(info, file)
                    print(parent_name + "'s client changed to " + client)
                    return
                
                else:
                    print("Unknown arguements passed. Use 'gd reset -h' for help.")
                        
                    
            elif len(args)==1:
                
                if not exists_bool:
                    print("current username : '"+ user_name + "' is deleted from the system.")
                    print("Recommended to change the user_name.")
                    print("------")
                
                drive_name = info[parent_name][3]
                drive_id = info[parent_name][4]
                    
                prompt = ''
                while prompt!='y' and prompt!='n':
                    prompt = input("Change user_name for this parent ? [y/n] : ")
                
                if prompt!='n':
                    create_info(info, parent_name=parent_name)
                    info = check_info()                
                else:
                    if not exists_bool:
                        print("------\ncannot change parent unless username is reset")
                        print("current username : '"+ user_name + "' is deleted from the system.")
                        print("------")
                        print("Possible soultions :")
                        print("+ Delete this parent : 'gd reset "+ parent_name + " -d'")
                        print("+ Reset the user for this parent : 'gd reset " + parent_name + " -user'")
                        return
                
                prompt = ''
                while prompt!='y' and prompt!='n':
                    prompt = input("Change path for this parent ? [y/n] : ")
                    
                if prompt!='n':
                    print('Example folder path : folder_in_root/subfolder1/subfolder2')
                    parent_path = input("Enter drive folder path : ")
                    if "'" in parent_path or "\"" in parent_path:
                        parent_path = parent_path[1:-1]
                    
                    create_info(info, parent_path, parent_name=parent_name, drive_name=drive_name, drive_id=drive_id, same_user=True)
                    print("\n" + parent_name + "'s path changed. Use 'gd status' to check.")
                    info = check_info()
                
                prompt = ''
                while prompt!='y' and prompt!='n':
                    prompt = input("Set this parent as default ? [y/n] : ")
                    
                if prompt!='n':
                    prev_def = info['default_parent']
                    info['default_parent'] = parent_name
                    if parent_name == prev_def:
                        print("'" + parent_name +"' is already the default parent.")
                    else:
                        with open(INFO_PATH, 'w') as file:
                            json.dump(info, file)
                        print("Default changed from '" + prev_def + "' to '" + parent_name +"'.")
                
                return
                
            else:
                print("Extra arguements found : use 'gd reset -h' for help.")
                return        
         

#-------------------------------------------------------
def status(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Displays parent information, staged paths and usernames registered.
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    information : list
        Depends on the arguements passed.  
    

    Notes
    ----------
    The following commands go into args :
        
    0. '-h' / -h  or '-help' / -help : shows help
    
    1. status([]) / gd status
        displays parent details and staged files
        
        Returns (if imported) : List with contents as shown below
                    [<dictionary as in .gdinfo.json>,
                    <list of existing staged paths>,
                    <list of missing or non-existing staged paths>]
        
    2. status(['-stage']) / gd status -stage
        displays only stage contents
        
        Returns (if imported) : List with contents as shown below
                    [<list of existing staged paths>,
                    <list of missing or non-existing staged paths>]
    
    3. status(['-users']) / gd status -users
        displays all users registered on the system
        
        Returns (if imported) : List with contents as shown below
                    [<user_names>]
                    
    4. status(['-clients']) / gd status -clients
        displays all client secrets or APIs registered on the system
        
        Returns (if imported) : List with contents as shown below
                    [<names of client secrets json files>]
    

    Examples
    ----------
    status([])          / gd status

    status(['-stage'])  / gd status -stage

    status(['-users'])   / gd status -users 

    status(['-clients'])   / gd status -clients 
    
    """

    
    if '-h' in args or '-help' in args:
        print(status.__doc__)
        return
    
    if '-users' in args:
        return ls(['-users'])
    
    if '-clients' in args:
        return ls(['-clients'])
    
    info = check_info()
    
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
            
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    return_list = [info]
    
    if not '-stage' in args and not RETURN_RESULT:
        print("---------------\nParent dicts :\n---------------")
        for par in parent_list:
            user_name = info[par][0]
            
            if par == info['default_parent']:
                print("// " + par + " // <DEFAULT>")
            else:
                print("// " + par + " //")
            
            print('username : ' + user_name)
            print("path     : '" + info[par][1] + "'")
            print("id       : '" + info[par][2] + "'")
            print("drive    : '" + info[par][3] + "'")
            print("driveId  : '" + info[par][4] + "'")
            print("client_sec : '" + info[par][5] + "'\n")
    
    existing_paths = []
    miss_paths = []
    with open(STAGE_PATH, 'r') as file:
        stage_list = file.readlines()
    
    if not RETURN_RESULT:
        if len(stage_list)==0:
            print("No files/folders staged.")
            return
        
        print("---------------\nStaged paths :\n---------------")
    
    for i in stage_list:
        i = i.rstrip()
        if os.path.exists(i):
            if not RETURN_RESULT:
                print(i)
            existing_paths.append(i)
        else:
            miss_paths.append(i)
    
    if not RETURN_RESULT:
        if not len(miss_paths)==0:
            print("\nThe following staged paths do not exist : \n---")
            for i in miss_paths:
                print(i)
        
        return
    
    return_list += [existing_paths, miss_paths]
    return return_list
    
    
#----------------------------------------------
def ls(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    list files/folder names in the parent_path or specified path
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    information : list
        List as shown here for files -
            [file_paths_list, file_ids_list]
        
        List of usernames when -users is used
        
        List of names of client secrets json files when -clients is used.
        
        List of shared drives for a <username> when -shared is used, as shown below -
            [drive_names_list, drive_ids_list]
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    1. ls([])   /   gd ls
        shows files/folders in the <default> parent cwd
    
    2. ls(['<parent_name>',])   /   gd ls <parent_name>
        If no arg. after '<parent_name>', it shows files or folders in the <parent_name> cwd
        
        '<path>' / <path> : shows files/folders in <path> in the <parent_name>
        
        '-a' / -a    : shows files/folders in parent_name and/or path with ids
            
    3. ls(['-users'])   /   gd ls -users
        shows all usernames registered in the SYSTEM
    
    4. ls(['-users'])   /   gd ls -users
        shows all usernames registered in the SYSTEM
        
    5. ls(['-shared', '<username>'])   /  gd ls -shared <username>
        shows all shared drives in <user_name>
        

    Examples
    ----------
    ls([])                          /   gd ls

    ls(['origin', '-path', '-a'])   /   gd ls origin -path -a

    ls(['-info'])                   /   gd ls -info

    ls(['-users'])                  /   gd ls -users

    ls(['-shared', '<username>'])   /   gd ls -shared <username>
    
    """
    
    if '-h' in args or '-help' in args:
        print(ls.__doc__)
        return
    
    if '-shared' in args:
        if len(args)==1:
            print("username arguement required. Try 'gd ls -h' for help.")
            return
        elif len(args)>2:
            print("Extra arguements passes. Try 'gd ls -h' for help.")
            return
        else:
            user_name = args[1]
            _, user_exists = check_user_name(user_name=user_name)
            
            if not user_exists:
                print("The username : '" + user_name + "'is not registered. Add a new parent using 'gd init -add' to register username.")
                return
            
            auth_from_cred(gauth, user_name)
            drives_list = gauth.service.drives().list().execute()['items']
            
            if RETURN_RESULT:
                return [ [i['name'] for i in drives_list], [i['id'] for i in drives_list] ]
                
            print("---------------------------------------")
            print("Shared Drive" + "    :    " + "driveId")
            print("---------------------------------------")
            
            for dic in drives_list:
                drive_name = dic['name']
                drive_id = dic['id']
                print(drive_name + "    :    " + drive_id)
           
            return
    
    if '-users' in args:
        
        if not os.path.exists(CRED_MAP_PATH):
            print("No gdrive credentials found on this system.")
            return
        
        with open(CRED_MAP_PATH, 'r') as file:
            creds_list = file.read().split(' ')
        
        users_list = []
        for user_name in creds_list:
            if len(user_name)<16 and len(user_name)>6:
                if RETURN_RESULT:
                    users_list.append(user_name)
                    continue
                
                print('+  ' + user_name)
                
        if RETURN_RESULT:
            return users_list
        
        return
    
    if '-clients' in args:
        #List of client files
        CLIENT_SECRETS_LIST = os.listdir(CLIENT_SECRETS_DIR)
        clients_list = [re.split(".json", i)[0] for i in CLIENT_SECRETS_LIST]

        if not os.path.exists(CLIENT_SECRETS_DIR) or len(clients_list)==0:
            print("No client secrets files found on this system")
            return
        
        if RETURN_RESULT:
            return clients_list
        
        for client in clients_list:
            print('+  ' + client)
        
        return
    
    info = check_info()
    show_ids = False
    
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parents_list = list(info.keys())
    parents_list.remove('default_parent')
    
    if '-a' in args:
        show_ids = True
        args.remove('-a')
        
    if len(args)==0:
        parent_name = info['default_parent']
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]
        auth_from_cred(gauth, user_name, client)
        drive = GoogleDrive(gauth)
    
    else:
        
        if len(args)==2:
            parent_name = args[0]
            drive_path = '/'.join(re.split('[\\\\/]', args[1]))
                
            if CURR_HOME_DIR in drive_path :
                drive_path = drive_path.split(CURR_HOME_DIR)[-1]
                
            if not parent_name in parents_list:
                print("'" + parent_name + "' : parent name not defined before.")
                return
            
            [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]  
            auth_from_cred(gauth, user_name, client)
            drive = GoogleDrive(gauth)
            
            #---------------DEBUGGING REQ---------------------
            if drive_path.startswith('/'):
                drive_path = '~/' + drive_path[1:]
                
            if CURR_HOME_DIR in drive_path:
                drive_path = drive_path.split(CURR_HOME_DIR)[-1]
              
            if drive_path=='/':
                drive_path = '~'
            #----------------------------------------------------
            drive_path = parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
            
            new_parent_id = get_path_ids(drive_path, drive, create_missing_folders = False, path_to = 'folder', default_root=drive_id)[-1]
            new_parent_path = drive_path            
            
            parent_path = new_parent_path
            parent_id = new_parent_id
            
        
        elif len(args) == 1:
            parent_name = args[0]
            if not parent_name in parents_list:
                print("'" + parent_name + "' : parent name not defined before.")
                return
            else:
                [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]
                auth_from_cred(gauth, user_name, client)
                drive = GoogleDrive(gauth)
        else:
            
            print("Unexpected arguements : use 'gd ls -h' for help")
            return
    
    if RETURN_RESULT:
        file_paths_list, file_ids_list, _ = list_all_contents(parent_path, init_folder_id=parent_id, drive=drive, dynamic_show=False, tier = 'curr', show_ids=show_ids, default_root=drive_id)
        return file_paths_list, file_ids_list
    
    _, _, _ = list_all_contents(parent_path, init_folder_id=parent_id, drive=drive, dynamic_show=True, tier = 'curr', show_ids=show_ids, default_root=drive_id)


#--------------------------------------
def find(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Searched for file and folder names using a query

    Parameters
    ----------
    args : list
        list of arguement strings.

    Returns
    ----------
    information : tuple
        (list of paths, list of ids)

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    1. find(["<query>"])   /   gd find "<query>"
        Uses the <query> string to find the file in default parent path
    
    2. find(['<parent_name>', "<query>"])   /   gd find <parent_name> "<query>"
        Uses the <query> string to find the file in <parent_name>'s path
    
    3. find(["<query>", '-path', '<path>'])   /   gd find "<query>" -path <path>
        Finds the file in <path> specified. If no parent_name specified, default parent is considered.
    
    4. find(["<query>", -<tier>]) / gd find "<query>" -<tier>
        Finds the file/folder upto the specified <tier> in the file hierarchy.
        
        Only following arguements can be passed as -<tier>:
            
            '-<int>' / -<int> : if integer, upto that tier
            
            '-curr' / -curr : Current tier (same as tier = 1)
            
            '-all'  / -all  : all tiers
    
    Additional optional arguements:
    -path, -<tier>
     

    Examples
    ----------
    find(["*.jpg"])                 /   gd find "*.jpg"

    find(["*.*", '-path', 'folder1/folder2'])   /   gd find "*.*" -path folder1/folder2

    find(['origin2', '-4', "*.xlsx* and *.csv*"])          /   gd find origin2 -4 "*.xlsx and *.csv"

    """
    
    if '-h' in args or '-help' in args:
        print(find.__doc__)
        return
    
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parents_list = list(info.keys())
    parents_list.remove('default_parent')
    
    search_folder_path = None
    search_folder_id = None
    tier = 'curr'
    
    #path input
    if '-path' in args:
        try:
            path_idx = args.index('-path') + 1
            search_folder_path = args.pop(path_idx)
        except:
            print('No path provided.')
        
        #removes '-path' from args
        _ = args.pop(path_idx-1)
    
    #tier input    
    for iarg in args:
        if '-' in iarg:
            tier = iarg[1:]
            args.remove(iarg)
            break
    
    #converting tier to integer if not 'all' or 'curr'
    try:
        tier = int(tier)
    except:
        pass
    
    if len(args)==0 or len(args)>2:
        print("Invalid number of arguements passed. See gd find -help")
        return
    
    if len(args)==2:
        parent_name = args[0]
        if not parent_name in parents_list:
            print("The parent name entered doesnt not exist.")
            return
    
    else:
        parent_name = info['default_parent']
    
    #Authentication
    [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]
    auth_from_cred(gauth, user_name, client)
    drive = GoogleDrive(gauth)
    
    if search_folder_path == None:
        search_folder_path = parent_path
        search_folder_id = parent_id
        
    #query to find files
    find_query = args[-1]
    
    query_paths = query_to_paths(drive, find_query, search_folder_path, path_id=search_folder_id, 
                           tier=tier, default_root=drive_id)
    
    if RETURN_RESULT:
        return query_paths
    
    print("file id : file path\n-----------------------\n")
    for i in range(len(query_paths[0])):
        print(query_paths[1][i] + ' : ' + query_paths[0][i])
        
    print("")


#-----------------------------------------
def cd(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Changes parent_paths (the cwd paths of parents)
    

    Parameters
    ----------
    args : list
        List of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders or files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    The <path> being passed need no be limited to be within the parent_path folder.
    It can to any file or folder within current driveID.
    It can be relative to the parent_path or can be absolute wrt to driveId.
    
    1. cd(['<path>'])  /  gd cd <path>
        changes cwd to <path> for default parent
    
    2. cd(['<parent_name>', '<path>'])  / gd cd <parent_path> <path>
        changes cwd to <path> for <parent_name>
    

    Examples
    ----------
    cd(['<path>'])                  /  gd cd <path>

    cd(['<parent_name>', '<path>']) /  gd cd <parent_name> <path>
    
    """
    
    if '-h' in args or '-help' in args:
        print(cd.__doc__)
        return
    
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    if len(args)==1:
        parent_name = info['default_parent']
        drive_path = args[0]
    
    elif len(args)==2:
        parent_name = args[0]
        drive_path = args[1]

    [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]  
    auth_from_cred(gauth, user_name, client)
    drive = GoogleDrive(gauth)
    
    drive_path = '/'.join(re.split('[\\\\/]', drive_path))
    
    #---------------DEBUGGING REQ---------------------
    if drive_path.startswith('/'):
        drive_path = '~/' + drive_path[1:]
        
    if CURR_HOME_DIR in drive_path:
        drive_path = drive_path.split(CURR_HOME_DIR)[-1]
      
    if drive_path=='/':
        drive_path = '~'
    #----------------------------------------------------
    drive_path = parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
    
    new_parent_id = get_path_ids(drive_path, drive, create_missing_folders = False, path_to = 'folder', default_root=drive_id)[-1]
    new_parent_path = drive_path
            
    info[parent_name][:5] = [user_name, new_parent_path, new_parent_id, drive_name, drive_id]
    print(parent_name + " cwd changed to '" + new_parent_path + "'")
    with open(INFO_PATH, 'w') as file:
        json.dump(info, file)

#------------------------------
def rm(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Deletes the file or folder at specified path in Google Drive
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders or files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    The <path> being passed need no be limited to be within the parent_path folder.
    
    It can to any file or folder within current driveID.
    
    It can be relative to the parent_path or can be absolute wrt to driveId.
    
    1. rm(['<path>'])   /   gd rm <path>
        trashes files or folders at the parent_path in <default> parent
    
    2. rm(['<parent_name>', '<path>'])  /  gd rm <parent_name> <path>
        trashes files or folders in <path> in <parent_name> parent
        
    3. rm(['<parent_name>', '<path>, '-f'])  /  gd rm <parent_name> <path> -f
        Permanently deletes files or folders in <path> in the <parent_name>
        

    Examples
    ----------
    rm(['<parent_name>', '<path>'])      /  gd rm <parent_name> <path>

    rm(['<parent_name>', '<path>, '-f']) /  gd rm <parent_name> <path> -f
    
    """
    
    if '-h' in args or '-help' in args:
        print(rm.__doc__)
        return
        
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    hard_delete= False
    
    if '-f' in args:
        args.remove('-f')
        hard_delete = True
    
    parents_list = list(info.keys())
    parents_list.remove('default_parent')
        
    if len(args)==2:
        parent_name = args[0]
        drive_path = '/'.join(re.split('[\\\\/]', args[1]))
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]  
        
    elif len(args)==1:
        parent_name = info['default_parent']
        drive_path = '/'.join(re.split('[\\\\/]', args[0]))
        
        if not parent_name in parents_list:
            print("'" + parent_name + "' : parent name not defined before.")
            return
        
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name] 
    
    elif len(args) == 0:
        parent_name = info['default_parent']
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]
        drive_path = parent_path
    
    else:
        print("Extra arguements passed. Try 'gd rm -h'.")
        return
    
    auth_from_cred(gauth, user_name, client)
    drive = GoogleDrive(gauth)
    prompt = 'y'
    
    #---------------DEBUGGING REQ---------------------
    if drive_path.startswith('/'):
        drive_path = '~/' + drive_path[1:]
        
    if CURR_HOME_DIR in drive_path:
        drive_path = drive_path.split(CURR_HOME_DIR)[-1]
      
    if drive_path=='/':
        drive_path = '~'
    #----------------------------------------------------
    drive_path = parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
    
    delete_id = get_path_ids(drive_path, drive, create_missing_folders = False, path_to = 'all', default_root=drive_id)[-1]
    delete_path = drive_path
    
    
    if delete_path == '' or delete_id == drive_id:
        prompt = input("WARNING: The entire drive will be deleted. Continue?[y/n] : ")
    elif delete_id == parent_id:
        prompt = input("All files in current parent will be deleted. Continue?[y/n]: ")
    
    if prompt=='y':
        delete(drive, drive_path=delete_path, drive_path_id=delete_id, hard_delete=hard_delete, default_root=drive_id)
    else:
        print("Delete action aborted.")
        
    
#----------------------------------        
def mkdir(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Makes an empty folder in specified path
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders or files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    The <path> being passed need no be limited to be within the parent_path folder.
    It can to any file or folder within current driveID.
    It can be relative to the parent_path or can be absolute wrt to driveId.
    
    1. mkdir(['<path>']) / gd mkdir <path>
        creates folder at the path in default parent
    
    2. mkdir(['<parent_name>', '<path>'])  /  gd mkdir <parent_ame> <path>
        creates folder at the path in <parent_name> parent
        

    Examples
    ----------
    mkdir(['<path>'])                  /  gd mkdir <path>
    
    mkdir(['<parent_name>', '<path>']) /  gd mkdir <parent_name> <path>
    
    """    

    if '-h' in args or '-help' in args:
        print(mkdir.__doc__)
        return
        
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parents_list = list(info.keys())
    parents_list.remove('default_parent')
        
    if len(args)==0:
        print("No path given. Check 'gd mkdir -h'.")
        return
    
    elif len(args)>2:
        print("Extra arguements passed. Check 'gd mkdir -h'.")
        return
    
    else:
        drive_path = '/'.join(re.split('[\\\\/]', args[-1]))
        if len(args)==1:
            parent_name = info['default_parent']
        else:
            parent_name = args[0]
            if not parent_name in parents_list:
                print("'" + parent_name + "' : parent name not defined before.")
                return
        
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]  
        auth_from_cred(gauth, user_name, client)
        drive = GoogleDrive(gauth)
        
        #---------------DEBUGGING REQ---------------------
        if drive_path.startswith('/'):
            drive_path = '~/' + drive_path[1:]
            
        if CURR_HOME_DIR in drive_path:
            drive_path = drive_path.split(CURR_HOME_DIR)[-1]
          
        if drive_path=='/':
            drive_path = '~'
        #----------------------------------------------------
        drive_path = parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
        
        _ = get_path_ids(drive_path, drive, create_missing_folders = True, path_to = 'folder', default_root=drive_id)[-1]
    
    return


#----------------------------------------------------------------------------------------
# 2. PUSH/PULL FUNCTIONS:
# This set of functions used to download/upload files/folder from/to Google Drive
#----------------------------------------------------------------------------------------
def add(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Adds paths to stage for pushing to Google Drive.
    This function just adds the paths to .gdstage file. It doesn't push any file.
    For pushing, use function push() / gd push after adding.
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders/files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    The <path> must be in local system
    
    1. add(['<path1>', '<path2>', '<path3>', ...]) / gd add <path1> <path2> <path3> ...
        adds multiple <path>s to the gd stage
    
    2. add(['-clear'])   /   gd add -clear
        clears all paths in the stage
    

    Examples
    ----------
    add(['<path1>', '<path2>', '<path3>', ...]) / gd add <path1> <path2> <path3> ...
    
    add(['-clear'])                             / gd add -clear
    
    """ 

    if '-h' in args or '-help' in args:
        print(add.__doc__)
        return
    
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    if '-clear' in args:
        with open(STAGE_PATH, 'w') as file:
            pass
        
        return
    
    with open(STAGE_PATH, 'a') as file:
        
        for i, path in enumerate(args):
            
            if "'" in path or "\"" in path:
                stage_path = path[1:-1]
            
            if HOME_DIR in path:
                stage_path = path
            else:
                stage_path = os.path.join(CURR_PATH, path)
            
            if os.path.exists(stage_path):
                file.write(stage_path + '\n')
            else:
                print(stage_path + " doesnt exist.")
     
#-----------------------------------------
def push(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Pushes or uploads files into path of the parent_name specified.
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders or files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    1. push([]) / gd push
        Pushes staged files to default parent
    
    2. push(['<parent_name1>', '<parent_name2>', '<parent_name3>', ... ]) / gd push <parent_name1> <parent_name2> <parent_name3> ...
        Pushes staged files to <parent_name> folder
    
    Optional arguements if pushed files already exist on drive-

    '-c' :  creates copy
    '-s' :  skip
    '-o' :  overwrites existing file
    '-i' :  prompt for each file  (DEFAULT)
    

    Examples
    ----------
    push(['-i'])                                     / gd push -i
    
    push(['<parent_name1>', '-s', '<parent_name2>']) / gd push <parent_name1> -s <parent_name2>
    
    """
    
    if '-h' in args or '-help' in args:
        print(push.__doc__)
        return
    
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    
    with open(STAGE_PATH, 'r') as file:
        stage_list = file.readlines()
        
    if len(stage_list)==0:
        print("No staged files. Use 'gd add <paths>' first")
        return
    
    #Default : asks the user
    prompt = 'ask'
    
    if '-s' in args:
        args.remove('-s')
        prompt = 's' #skips
    
    if '-o' in args:
        args.remove('-o')
        prompt = 'o' #overwrite
        
    if '-c' in args:
        args.remove('-c')
        prompt = 'c' #creates_copy
        
    if '-i' in args:
        args.remove('-i')
        prompt = 'ask' #asks each time
    
    miss_paths = []
    
    if len(args)==0:
        parent_name = info['default_parent']
        [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]  
        
        print("---------------\n" + parent_name + "\n---------------")
        auth_from_cred(gauth, user_name, client)
        drive = GoogleDrive(gauth)
        
        for path in stage_list:
            path = path.rstrip()
            if os.path.exists(path):
                if os.path.isdir(path):
                    upload(path, parent_path, drive, prompt=prompt, default_root=drive_id)
                else:
                    upload_file_by_id(path, parent_id, drive, prompt=prompt)
            else:
                miss_paths.append(path)
        
    else:
        
        for par in args:
            if not par in parent_list:
                print("'" + par + "' : parent name not defined before.")
                continue
            
            [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[par]
            
            print("---------------\n" + par + "\n---------------")
            auth_from_cred(gauth, user_name, client)
            drive = GoogleDrive(gauth)
            
            for path in stage_list:
                path = path.rstrip()
                if os.path.exists(path):
                    if os.path.isdir(path):
                        upload(path, parent_path, drive, prompt=prompt, default_root=drive_id)
                    else:
                        upload_file_by_id(path, parent_id, drive, prompt=prompt)
                else:
                    miss_paths.append(path)
                    
    if not len(miss_paths)==0:
        print("---\n These paths in stage list are missing : \n")
        for i in miss_paths:
            print(i)
 
#-----------------------------------------        
def pull(args):
    """
    [syntax when imported / syntax when called via CMD]
    
    Pulls or downloads files from drive
    

    Parameters
    ----------
    args : list
        list of arguement strings.
    

    Returns
    ----------
    None
        Edits the folders or files on local system
    

    Notes
    ----------
    The following commands go into args :
    
    0. '-h' / -h  or '-help' / -help : shows help
    
    The <path> being passed need no be limited to be within the parent_path folder.
    It can to any file/folder within current driveID.
    It can be relative to the parent_path or can be absolute wrt to driveId.
    
    1. pull([]) / gd pull
        Downloads complete default parent folder to current dir.
    
    2. pull(['<parent_name>']) / gd pull <parent_name>
        Downloads complete <parent_name> folder to current dir. If arguements
        passed in the list, then the first arguement must always be the parent name
    
    3. pull(['<parent_name>', '<path1>', <path2>, <path3>, ...]) / gd pull <parent_name> <path1> <path2> <path3> ...
        Downloads all the paths specified into current dir from the username
        related to this parent.
        
    4. push(['<parent_name>', '-id', '<path_id1>', '<path_id2>', ...]) / gd pull <parent_name> -id <path_id1> <path_id2> ...
        Use of '-id' : Downloads from all the path_ids specified into current dir from the username
        related to this parent.
        
    5. push(['<parent_name>', '-dest', '<save_path>']) / gd pull <parent_name> -dest <save_path>
        Use of '-dest' : downloads into <save_path> in local system specified from parent_path")
    

    Optional arguements if pulled files already exist on local system -
    
    '-c' :  creates copy
    '-s' :  skip
    '-o' :  overwrites existing file
    '-i' :  prompt for each file (DEFAULT)
    

    Examples
    ----------
    pull(['-i']) / gd pull -i

    pull(['<parent_name>', '<path1>', <path2>, '-s', '-id', 'id3', '-dest', '<save_path>']) / gd pull <parent_name> <path1> <path2> -s -id <id3> -dest <save_path>
    
    """
    
    if '-h' in args or '-help' in args:
        print(pull.__doc__)
        return
        
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    is_id = False #Checks if path given or id given
    
    #Default : asks the user
    prompt = 'ask'
    
    if '-s' in args:
        args.remove('-s')
        prompt = 's' #skips
    
    if '-o' in args:
        args.remove('-o')
        prompt = 'o' #overwrite
        
    if '-c' in args:
        args.remove('-c')
        prompt = 'c' #creates_copy
        
    if '-i' in args:
        args.remove('-i')
        prompt = 'ask' #asks each time
        
    if len(args)>0:
        parent_name = args[0]
        args.remove(parent_name)
        if not parent_name in parent_list:
            print("Parent : " + parent_name + " not found. Add parent using 'gd init -add' before pulling.")
            return
    else:
        parent_name = info['default_parent']
        
    [user_name, parent_path, parent_id, drive_name, drive_id, client] = info[parent_name]
    auth_from_cred(gauth, user_name, client)
    drive = GoogleDrive(gauth)
    
    #Initializing drive_path params
    drive_path_list = [parent_path]
    drive_path_id_list = [None]
    save_path = CURR_PATH #default save path is current working directory
    
    if '-dest' in args:
        dest_index = args.index('-dest')
        save_path = args[dest_index+1]
        args.remove('-dest')
        args.remove(save_path)
        
    if '-id' in args:
        is_id = True
        id_index = args.index('-id')
        drive_path_id_list = args[id_index+1:]
        drive_path_list = [None for i in drive_path_id_list]
        args.remove('-id')
        for i in drive_path_id_list:
            args.remove(i)
    
    if len(args)>0:
        if is_id:
            drive_path_list += args
            drive_path_id_list += [None for i in drive_path_list]
        else:
            drive_path_list = args
            drive_path_id_list = [None for i in drive_path_list]    
    
    for drive_path, drive_path_id in zip(drive_path_list, drive_path_id_list):    
        
        #parsing drive_path
        #---------------DEBUGGING REQ---------------------
        if drive_path.startswith('/'):
            drive_path = '~/' + drive_path[1:]
            
        if CURR_HOME_DIR in drive_path:
            drive_path = drive_path.split(CURR_HOME_DIR)[-1]
          
        if drive_path=='/':
            drive_path = '~'
        #----------------------------------------------------
        drive_path = parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
        
        #parsing save_path
        if "'" in save_path or "\"" in save_path:
            save_path= save_path[1:-1]
        if not HOME_DIR in save_path: #This means if it is relative path
            save_path = os.path.join(CURR_PATH, save_path)       
        
        #Checking if save_path exists
        if not os.path.exists(save_path):
            print("The path : '" + save_path + "' doesn't exist.")
            return
        
        download(drive, drive_path=drive_path, drive_path_id=drive_path_id, download_path=save_path, prompt=prompt, default_root=drive_id)    

    
    
#------------------------------------------------------------------------------------------------
#Miscelleneous functions
#------------------------------------------------------------------------------------------------
def help(args):
    """displays help text (if imported, args = [])"""
    print(help_text)

def rmgd(args):
    """removes the created gd file (if imported, args = [])"""
    os.remove(os.path.join(ROOT_PATH, 'gd'))

def default(args):
    """brings the package to its default (if imported, args = [])"""
    shutil.rmtree(CREDS_DIR)
    rmgd(args)

    
#-------------------------------------------------------------------------------------------------
#COMMAND-LINE INTERACTION
#-------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    #When gd.py is called from command line
    
    #Parsing Command-line arguements
    parser = argparse.ArgumentParser(description=help_text, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('func')
    parser.add_argument('args', nargs = argparse.REMAINDER)
    args_func = parser.parse_args()
    
    #func is the main function
    func = args_func.func
    args = args_func.args
    
    RETURN_RESULT = False
    try:
        exec( func + '(args)' )
    #sometimes token fails to refresh
    except:
        exec( func + '(args)' )
    """
    except errors.HttpError:
        delete_cred_files()
        exec( func + '(args)' )
    
    except Exception as e:
        print(e)
    """
else:
    #When gd.py is imported
    RETURN_RESULT = True