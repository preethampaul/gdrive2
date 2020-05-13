# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:43:40 2020
@author: Preetham
"""
import argparse
import os
import json
import re
import shutil

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.apiattr import ApiResourceList
from apiclient import errors

import util

#Important objects for gdrive
gauth = GoogleAuth()    #for authentication
drive = GoogleDrive(gauth) #for drive utilities

#Current Working Directory
CURR_PATH = os.getcwd()

#Local Home directory
CURR_HOME_DIR = '/'.join(re.split('[\\\\/]', os.path.expanduser('~')))

#gd Code paths
HOME_DIR = re.split("[\\\\/]", CURR_PATH)[0]
ROOT_PATH = os.path.dirname(__file__)

#Info paths in current directory
INFO_FOLDER = os.path.join(CURR_PATH,'.gd')
INFO_PATH = os.path.join(INFO_FOLDER, '.gdinfo.json')
STAGE_PATH = os.path.join(INFO_FOLDER, '.gdstage')

#Credentials path
CLIENT_SECRETS = 'client_secrets.json'
CRED_MAP = 'creds'
CREDS_DIR = os.path.join(ROOT_PATH, 'api_data')

CRED_MAP_PATH = os.path.join(CREDS_DIR, CRED_MAP)
CLIENT_SECRETS_PATH = os.path.join(CREDS_DIR, CLIENT_SECRETS)


#Deafult info during initialization
DEFAULT_INFO = {
        'default_parent' : 'origin',
        'origin' : ['no_user', '', 'root', 'My Drive', 'root']
        #parent_name : [user_name, parent_path, parent_id, drive_name, drive_id]
        }

#Text to show for 'gd -help'
help_text = "\n\
<func> = function name\n\
<args> = arguements\n\n\
Overview of initializing/listing fucnctions:\n\
--------------------------------\n\
'init'   : initialize gdrive, add new parents to initialized dir.\n\
'status' : show parents list, show stage list\n\
'reset'  : change default parent,\n\
           change user_names, paths of parents, parent root folders (Ex: shared drives)\n\
           delete parents, delete authentication data\n\
'ls'     : list_all files/folders in parent paths, shows registered users and shared drives\n\
'cd'     : changes parent_path directly without using 'reset' function\n\
\n\
Overview of push/pull functions:\n\
---------------------------------\n\
'add'    : add paths to the stage, clear stage\n\
'push'   : upload files/folders to parent_paths\n\
'pull'   : download files/folders from parent_paths\n\n\
"


#UTILITY-FUNCTIONS----------------------------------------------------------------------
#These are used in main command functions
#---------------------------------------------------------------------------------------


def check_user_name(user_name=None):
    
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
                
    
        if util.check_creds_list(user_name, check_only=True):
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
    
    if len(info) == 0:
        #default values
        util.create_folders_path(INFO_FOLDER)
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
        
    util.auth_from_cred(gauth, info[parent_name][0])
    drive = GoogleDrive(gauth)
    info[parent_name][2] = util.get_path_ids(parent_path, drive, create_missing_folders = False, path_to = 'folder', default_root=drive_id)[-1]
    
    with open(INFO_PATH, 'w') as file:
        json.dump(info, file)

#---------------------------------------------
def check_parent_name():
    
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

def delete_cred_files():
    file_list = os.listdir(CREDS_DIR)
    file_list.remove(CLIENT_SECRETS)
    file_list.remove(CRED_MAP)
    
    for i in file_list:
        os.remove(os.path.join(CREDS_DIR, i))

#USAGE-FUNCTIONS------------------------------------------------------------------------------------
#These are the main command functions called from terminal
#---------------------------------------------------------------------------------------------------
    
def init(args):
    
    if '-h' in args or '-help' in args:
        print("gd init [-add]")
        print("\nDescription: creates new parent info")
        print("------\n")
        print("'gd init'      : initialzes the current directory for gdrive")
        print("'gd init -add' : adds new parent to the current directory")
        return
    
    info = check_info()
    parent_name = DEFAULT_INFO['default_parent']
    
    if len(info)==0:
        
        if not len(args)==0:
            print('gdrive not initialized in this folder. Try command : gd init')
            return
        
        create_info(info)
        return
    
    elif '-add' in args:
        parent_name = check_parent_name()
        create_info(info, parent_name=parent_name, same_user=False)
        print(parent_name + " : new parent created.")
        
        return
            
    elif not len(args) == 0:
        print("Command unknown.")
        print("Expected commands : gd init [-add]")
        return
              
#------------------------------------------
def reset(args):
    
    if '-h' in args or '-help' in args:
        print("gd reset <parent_name> [-user, -path, -drive, -d, -default]")
        print("gd reset -info")
        print("gd reset -user [<user_name>, -a]")
        print("\nDescription: changes the parent information for the curr dir.")
        print("------\n")
        print("'gd reset <parent_name>'       : prompts inputs for user_name, path and")
        print("                                 default prop. of existing parent")
        print("'gd reset <parent_name> -user' : resets user_name/account in the parent name given.")
        print("'gd reset <parent_name> -path' : resets path in the parent name given.")
        print("'gd reset <parent_name> -drive': resets drive in the parent name given (useful to set shared drives as roots)")
        print("'gd reset <parent_name> -d'    : deletes parent name given and its path, user_name and id")
        print("'gd reset <parent_name> -default': set parent name given as 'default'")
        print("'gd reset -info'               : erases all parents and user_names for current directory and re-initializes")
        print("'gd reset -user <user_name>'   : deletes <user_name>'s authentication data in the SYSTEM")
        print("'gd reset -user -a'            : deletes all users authentication data in the SYSTEM")
        
        return
    
    
    info = check_info()
    
    if not ('-user' in args and '-a' in args): 
        
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
                        api_folder_path = os.path.join(ROOT_PATH, 'api_data')
                        file_list = os.listdir(api_folder_path)
                        if 'client_secrets.json' in file_list:
                            file_list.remove('client_secrets.json')
                        
                        for i in file_list:
                            os.remove(os.path.join(api_folder_path, i))
                        
                        if os.path.exists(INFO_PATH):
                            shutil.rmtree(INFO_FOLDER)
                            print("All authentication data deleted. Use `gd init` to re-initialize.")
                        
                        return
                    
                elif exists_bool:
                    with open(CRED_MAP_PATH, 'r') as file:
                        creds_list = file.read().split(' ')
                    
                    cred_id = creds_list[creds_list.index(user_name) + 1]
                    cred_path = os.path.join(ROOT_PATH, 'api_data', cred_id)
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
            
                    util.auth_from_cred(gauth, user_name)
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
    
    if '-h' in args or '-help' in args:
        print("gd status [-stage]")
        print("\nDescription: Displays parent info")
        print("------\n")
        print("'gd status'          : displays parent details and staged files")
        print("'gd status -stage'   : displays only stage contents")
        print("'gd status -user'    : displays all users registered on the system")
        return
    
    if '-user' in args:
        ls(['-users'])
        return
    
    info = check_info()
    
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
            
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    
    if not '-stage' in args:
        print("---------------\nParent dicts :\n---------------")
        for par in parent_list:
            user_name = info[par][0]
            char_len = len(user_name)
        
            stars = user_name[2:-1]
            """
            for i in range(char_len-3):
                stars = stars+'*'
            """
            
            if par == info['default_parent']:
                print("// " + par + " // <DEFAULT>")
            else:
                print("// " + par + " //")
            
            print('username : ' + user_name[0:2] + stars + user_name[-1])
            print("path    : '" + info[par][1] + "'")
            print("id      : '" + info[par][2] + "'")
            print("drive   : '" + info[par][3] + "'")
            print("driveId : '" + info[par][4] + "'\n")
    
    miss_paths = []
    with open(STAGE_PATH, 'r') as file:
        stage_list = file.readlines()
    
    if len(stage_list)==0:
        print("No files/folders staged.")
        return
    
    print("---------------\nStaged paths :\n---------------")
    for i in stage_list:
        i = i.rstrip()
        if os.path.exists(i):
            print(i)
        else:
            miss_paths.append(i)
    
    if not len(miss_paths)==0:
        print("\nThe following staged paths do not exist : \n---")
        for i in miss_paths:
            print(i)
        
#----------------------------------------------
def ls(args):
    
    if '-h' in args or '-help' in args:
        print("gd ls [<parent_name> [<path>]] [-a, -users, shared]")
        print("\nDescription: lists files in parents")
        print("------\n")
        print("'gd ls'                     : shows files/folders in the <default> parent cwd")
        print("'gd ls <parent_name>'       : shows files/folders in the <parent_name> cwd")
        print("'gd ls <parent_name> <path>'       : shows files/folders in <path> in the <parent_name>")
        print("'gd ls [<parent_name>] [path] -a'  : shows files/folders in [<parent_name>, <default>],[path] with ids")
        print("'gd ls -users'                     : shows all usernames registered in the SYSTEM")
        print("'gd ls -shared <user_name>'        : shows all shared drives in <user_name>")
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
            
            util.auth_from_cred(gauth, user_name)
            drives_list = gauth.service.drives().list().execute()['items']
            
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
        
        for user_name in creds_list:
            if len(user_name)<16 and len(user_name)>6:
                print('+  ' + user_name)
        
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
        [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]
        util.auth_from_cred(gauth, user_name)
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
            
            [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]  
            util.auth_from_cred(gauth, user_name)
            drive = GoogleDrive(gauth)
            
            #---------------DEBUGGING REQ---------------------
            if drive_path.startswith('/'):
                drive_path = '~/' + drive_path[1:]
                
            if CURR_HOME_DIR in drive_path:
                drive_path = drive_path.split(CURR_HOME_DIR)[-1]
              
            if drive_path=='/':
                drive_path = '~'
            #----------------------------------------------------
            drive_path = util.parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
            
            new_parent_id = util.get_path_ids(drive_path, drive, create_missing_folders = False, relative_id = None, path_to = 'folder', default_root=drive_id)[-1]
            new_parent_path = drive_path            
            
            parent_path = new_parent_path
            parent_id = new_parent_id
            
        
        elif len(args) == 1:
            parent_name = args[0]
            if not parent_name in parents_list:
                print("'" + parent_name + "' : parent name not defined before.")
                return
            else:
                [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]
                util.auth_from_cred(gauth, user_name)
                drive = GoogleDrive(gauth)
        else:
            
            print("Unexpected arguements : use 'gd ls -h' for help")
            return
    
    _, _, _ = util.list_all_contents(parent_path, init_folder_id=parent_id, drive=drive, dynamic_show=True, tier = 'curr', show_ids=show_ids, default_root=drive_id)

#-----------------------------------------
def cd(args):
    
    if '-h' in args or '-help' in args:
        print("gd cd [<parent_name>] path")
        print("\nDescription: changes parent_paths")
        print("------\n")
        print("'gd cd <path>'              : changes cwd to <path> for default parent")
        print("'gd cd [<parent_name>] <path>'  : changes cwd to <path> for <parent_name>")
        
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

    [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]  
    util.auth_from_cred(gauth, user_name)
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
    drive_path = util.parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
    
    new_parent_id = util.get_path_ids(drive_path, drive, create_missing_folders = False, relative_id = None, path_to = 'folder', default_root=drive_id)[-1]
    new_parent_path = drive_path
            
    info[parent_name] = [user_name, new_parent_path, new_parent_id, drive_name, drive_id]
    print(parent_name + " cwd changed to '" + new_parent_path + "'")
    with open(INFO_PATH, 'w') as file:
        json.dump(info, file)

#------------------------------
def rm(args):
    
    if '-h' in args or '-help' in args:
        print("gd rm [<parent_name>, <path>] [-f]")
        print("\nDescription: lists files in parents")
        print("------\n")
        print("'gd rm <path>'       : trashes files/folders at the parent_path in <parent_name> parent")
        print("'gd rm [parent_name] <path>': trashes files/folders in <path> in <default> parent")
        print("'gd rm [parent_name] [path] -f': deletes files/folders in <path> in the <parent_name>")
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
        [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]  
        
    elif len(args)==1:
        parent_name = info['default_parent']
        drive_path = '/'.join(re.split('[\\\\/]', args[0]))
        
        if not parent_name in parents_list:
            print("'" + parent_name + "' : parent name not defined before.")
            return
        
        [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name] 
    
    elif len(args) == 0:
        parent_name = info['default_parent']
        drive_path = parent_path
    
    else:
        print("Extra arguements passed. Try 'gd rm -h'.")
        return
    
    util.auth_from_cred(gauth, user_name)
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
    drive_path = util.parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
    
    delete_id = util.get_path_ids(drive_path, drive, create_missing_folders = False, relative_id = None, path_to = 'all', default_root=drive_id)[-1]
    delete_path = drive_path
    
    
    if delete_path == '' or delete_id == drive_id:
        prompt = input("WARNING: The entire drive with be deleted. Continue?[y/n] : ")
    elif delete_id == parent_id:
        prompt = input("All files in current parent will be deleted. Continue?[y/n]: ")
    
    if prompt=='y':
        util.delete(drive, drive_path=delete_path, drive_path_id=delete_id, hard_delete=hard_delete, default_root=drive_id)
    else:
        print("Delete action aborted.")
        
#----------------------------------        
def mkdir(args):
    if '-h' in args or '-help' in args:
        print("gd mkdir [<parent_name>, <path>]")
        print("\nDescription: lists files in parents")
        print("------\n")
        print("'gd mkdir <path>'       : creates folder at the path in default parent")
        print("'gd mkdir [parent_name] <path>': creates folder at the path in <parent_name> parent")
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
        
        [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]  
        util.auth_from_cred(gauth, user_name)
        drive = GoogleDrive(gauth)
        
        #---------------DEBUGGING REQ---------------------
        if drive_path.startswith('/'):
            drive_path = '~/' + drive_path[1:]
            
        if CURR_HOME_DIR in drive_path:
            drive_path = drive_path.split(CURR_HOME_DIR)[-1]
          
        if drive_path=='/':
            drive_path = '~'
        #----------------------------------------------------
        drive_path = util.parse_drive_path(drive_path, drive, parent_id, default_root=drive_id)
        
        _ = util.get_path_ids(drive_path, drive, create_missing_folders = True, relative_id = None, path_to = 'folder', default_root=drive_id)[-1]
    
    return

#-----------------------------------------------------------------------------
#PUSH/PULL FUNCTIONS:
#-----------------------------------------------------------------------------
def add(args):
    
    if '-h' in args or '-help' in args:
        print("gd add <paths>,[-clear]")
        print("\nDescription: adds file to stage")
        print("------\n")
        print("'gd add <paths>' : adds multiple <path>s to the gd stage")
        print("'gd add -clear'  : clears the stage")
        
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
    
    if '-h' in args or '-help' in args:
        print("gd push [-s,-c,-o,-i] [parent_names]]")
        print("\nDescription: pushes/uploads files into drive")
        print("------\n")
        print("'gd push' : pushed staged files to default parent")
        print("'gd push <parent_name>'  :  ... to <parent_name> folder")
        print("\nUse the optional arguements if pushed files already exist on drive:")
        print("-c    :  creates copy (DEFAULT)")
        print("-s    :  skip")
        print("-o    :  overwrites existing file")
        print("-i    :  prompt each time")
        
        
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
        [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]  
        
        print("---------------\n" + parent_name + "\n---------------")
        util.auth_from_cred(gauth, user_name)
        drive = GoogleDrive(gauth)
        
        for path in stage_list:
            path = path.rstrip()
            if os.path.exists(path):
                if os.path.isdir(path):
                    util.upload(path, parent_path, drive, prompt=prompt, default_root=drive_id)
                else:
                    util.upload_file_by_id(path, parent_id, drive, prompt=prompt)
            else:
                miss_paths.append(path)
        
    else:
        for par in args:
            if not par in parent_list:
                print("'" + par + "' : parent name not defined before.")
                continue
            
            [user_name, parent_path, parent_id, drive_name, drive_id] = info[par]
            
            print("---------------\n" + par + "\n---------------")
            util.auth_from_cred(gauth, user_name)
            drive = GoogleDrive(gauth)
            
            for path in stage_list:
                path = path.rstrip()
                if os.path.exists(path):
                    if os.path.isdir(path):
                        util.upload(path, parent_path, drive, prompt=prompt, default_root=drive_id)
                    else:
                        util.upload_file_by_id(path, parent_id, drive, prompt=prompt)
                else:
                    miss_paths.append(path)
                    
    if not len(miss_paths)==0:
        print("---\n These paths in stage list are missing : \n")
        for i in miss_paths:
            print(i)
 
#-----------------------------------------        
def pull(args):
    
    if '-h' in args or '-help' in args:
        print("gd pull [-s,-c,-o,-i] [-id, -dest] [parent_names] [drive_path] [save_path]")
        print("\nDescription: pulls/downloads files from drive")
        print("------\n")
        print("'gd pull'                : downloads complete default parent folder to current dir.")
        print("'gd pull <parent_name>'  :  downloads complete <parent_name> folder to current dir.")
        print("\n'gd pull [<parent_name>] <drive_path>'  :  downloads drive_path into current dir.")
        print("'gd pull [<parent_name>] -id <drive_id>'  :  downloads from drive_id into current dir.")
        print("'gd pull [<parent_name>] -dest <save_path>'  :  downloads complete parent_path into <save_path>")
        print("\n'gd pull [<parent_name>] <drive_path> <save_path>'  :  downloads drive_path into save_path")

        print("\nUse the optional arguements if pushed files already exist on drive:")
        print("-c    :  creates copy (DEFAULT)")
        print("-s    :  skip")
        print("-o    :  overwrites existing file")
        print("-i    :  prompt each time")
        
        return
    
    info = check_info()
    if len(info) == 0:
        print('gd not initiated in this folder, try : gd init')
        return
    
    parent_list = list(info.keys())
    parent_list.remove('default_parent')
    is_id = False #Checks if path given or id given
    is_dest = False #Checks if path is destinations' or drive's
    
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
        
    if '-id' in args:
        args.remove('-id')
        is_id = True
        
    if '-dest' in args:
        args.remove('-dest')
        is_dest = True
    
    if len(args)>3:
        print("Extra arguements passed. Check 'gd push -h' for help")
        return

    elif len(args)==3:
        parent_name = args[0]
        args.remove(parent_name)
        if not parent_name in parent_list:
            print("Parent : " + parent_name + " not found. Add parent using 'gd init -add' before pulling.")
            return
    else:
        parent_name = info['default_parent']
        
    [user_name, parent_path, parent_id, drive_name, drive_id] = info[parent_name]
    util.auth_from_cred(gauth, user_name)
    drive = GoogleDrive(gauth)
    
    #Initializing drive_path params
    drive_path = parent_path
    drive_path_id = None
    save_path = CURR_PATH #default
    
    if len(args)>0:
        
        if len(args)==2:
            save_path = args[1]
            
        if is_dest:
            save_path = args[0]
        else:
            if is_id:
                drive_path_id = args[0]
                drive_path = None
            else:
                drive_path = args[0]
        
        if not drive_path == None:
            drive_path = '/'.join(re.split('[\\\\/]', drive_path))
            #relative paths
            if drive_path[0] == '/' or drive_path[0] == '\\':
                drive_path = parent_path + drive_path
        
        if "'" in save_path or "\"" in save_path:
            save_path= save_path[1:-1]
        
        if not HOME_DIR in save_path:
            save_path = os.path.join(CURR_PATH, save_path)       
    
    if not os.path.exists(save_path):
        print("The path : '" + save_path + "' doesn't exist.")
        return
    
    util.download(drive, drive_path=drive_path, drive_path_id=drive_path_id, download_path=save_path, prompt=prompt, default_root=drive_id)    

#----------------------
#COMMAND-LINE INTERACTION----------------------------------------

if __name__ == "__main__":
    #optional arguements
    opt_args=[]
    
    #Parsing Command-line arguements
    parser = argparse.ArgumentParser(description=help_text, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('func')
    parser.add_argument('args', nargs = argparse.REMAINDER)
    args_func = parser.parse_args()
    
    #func is the main function
    func = args_func.func
    args = args_func.args
    
    
    exec( func + '(args)' )
    """
    except errors.HttpError:
        delete_cred_files()
        exec( func + '(args)' )
    
    except Exception as e:
        print(e)
    """