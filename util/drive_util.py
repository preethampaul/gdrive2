# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 10:43:31 2020
@author: Preetham
"""

import os
import re
from time import sleep
from datetime import date

def dancing_dots(switch):
    """
    An attempt to create loading animation
    switch = 'on' shows one complete load animation
            = 'off' erases previous stdout line
    """
    char_len = 10
    
    if switch=='on':
        for i in range(0, char_len, 1):
            j = 0
            while j<i:
                print('-', end='')
                j+=1
            
            if j>=0 and j<char_len:
                print('|', end='')
                j+=1
                
            if j>=0 and j<char_len:
                print('O', end='')
                j+=1
                
            if j>=0 and j<char_len:
                print('|', end='')
                j+=1
            
            while j<char_len:
                print('-', end='')
                j+=1
                
            sleep(1)
            
            for j in range(char_len):
                print('\b', end='')
    
    elif switch=='off':
        
        for j in range(char_len):
                print('\b', end='')

def create_folders_path(path):
    """
    Creates non-existing folders along the local/system path
    Input = {
            path = path to a folder
            
    }
    Output = {
            returns None
        }
    """
    if os.path.exists(path) and not os.path.isdir(path):
        raise ValueError("path must lead to a folder if exists")
    
    path_list = re.split("[\\\\/]", path)
    curr_path = path_list[0]
    if not os.path.exists(curr_path):
        os.mkdir(curr_path)
    
    for path_j in path_list[1:]:
        curr_path = curr_path + '\\' + path_j
        if not os.path.exists(curr_path):
            os.mkdir(curr_path)

def create_folder(folder_name, parent_folder_id, drive):
    """
    Creates folder in drive with title = folder_name
    Input = {
            folder_name = name of folder
            parent_folder_id = ID of the parent folder
            drive = GoogleDrive object
    }
    Output = {
            returns the id of the created folder
        }
    """
    
    folder = drive.CreateFile({'parents' : [{'id' : parent_folder_id}],'mimeType' : 'application/vnd.google-apps.folder', 'title' : folder_name})
    folder.Upload()
    return folder['id']

def get_path_from_id(drive, file_id):
    
    path = ['']
    ids = []
    
    while file_id!='root':
        file = drive.CreateFile({'id' : file_id})
        file.FetchMetadata()
        path.append(file['title'])
        ids.append(file_id)
        
        if len(file['parents'])==0:
            break
        
        file_id = file['parents'][0]['id']
        
    ids.append('root')
    
    return '/'.join(path[::-1]), ids[::-1]

def get_id_by_name(name, parent_folder_id, drive, file_type = 'all'):
    
    """
    Returns list of ids for folders or files with title = name in the drive folder
    with id = parent_folder_id
    Input = {
            name = name of folder or file
            parent_folder_id = ID of the parent folder
            drive = GoogleDrive object
            file_type = 'folder' to return only folders' ids
                        'not-folder' to return ids other than folders
                        'all' to return all ids with the name [DEFAULT]
    }
    Output = {
            returns a tuple of 2 lists : (list of ids, list of corresponding mime types)
        }
    """
    
    try:
        file_list = drive.ListFile({'q' : "title = '" + name + "' and '" + parent_folder_id + "' in parents and trashed=false"}).GetList()
    except:
        file_list = []
        
    file_id_list = []
    file_mime_list = []
    
    for file in file_list:
        file_mime = file['mimeType']
        if file_type == 'folder' and file_mime == 'application/vnd.google-apps.folder':
            file_id_list.append(file['id'])
            file_mime_list.append(file_mime)
        elif file_type == 'not-folder' and file_mime != 'application/vnd.google-apps.folder':
            file_id_list.append(file['id'])
            file_mime_list.append(file_mime)
        elif file_type == 'all':
            file_id_list.append(file['id'])
            file_mime_list.append(file_mime)
        
    return file_id_list, file_mime_list

def get_path_ids(drive_path, drive, create_missing_folders = True, relative_id = None, path_to = 'folder'):
    
    """
    Returns list of ids for folders or files in the path to the drive_path
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
    The last id in this list will be of a folder or a file, which the user must determine
    with the path_to arguement
    
    Input = {
            drive_path = path to a file or folder in drive
            
            drive = GoogleDrive object
            
            create_missing_folders (a boolean input)
                = True if create the folders in the path if they dont exist
                = false returns a error if any of the folder in the path doesnt exist
            
            relative_id = None if absolute paths are desired
                        = <current working folder id> if relative paths are desired
            
            path_to = 'folder' to return only folders' ids [DEFAULT]
                'not-folder' to return ids other than folders
    }
    Output = {
            returns a list of all ids in the path like this :
                [Folder1_id, Folder2_id, Folder3_id] if path_to = 'folder'
                [Folder1_id, Folder2_id, File id] if path_to = 'not-folder'
                [Folder1_id, Folder2_id, 'no-file-found'] if path_to = 'not-folder'
                                            and the file at the end of path doesnt exist
                
    Gives error if there are more than one files or more than folders with same name
        }
    """
    #For root path
    if drive_path == '':
        return ['root']
    
    path_list = re.split('[\\\\/]', drive_path)
    path_id_list = path_list
    
    for i in range(len(path_list)):
        
        if i == 0:
            if relative_id == None:
                parent_folder_id = 'root'
            else:
                parent_folder_id = relative_id
        else:
            parent_folder_id = path_id_list[i-1]
        
        if i < len(path_list) - 1:
            path_id, _ = get_id_by_name(path_list[i], parent_folder_id, drive, file_type = 'folder')
        else:
            path_id, _ = get_id_by_name(path_list[i], parent_folder_id, drive, file_type = path_to)
        
        if len(path_id) > 1:
            raise NameError('More than one folder or file found with the same name : '+ path_list[i] +' in ' + '\\'.join(path_list[:i]))
        
        elif len(path_id) == 0:
            
            if i == len(path_list) - 1 and path_to == 'not-folder':
                path_id_list[i] = 'no-file-found'
                    
            elif create_missing_folders:
                path_id_list[i] = create_folder(path_list[i], parent_folder_id, drive)
            
            else:
                raise ValueError("path to file-type: '" + path_to +"' not found with name : "+ path_list[i] +" in '" + '\\'.join(path_list[:i]) + "'")
        
        else:
            path_id_list[i] = path_id[0]
        
    return path_id_list
 
    
def list_all_contents(init_folder_path, init_folder_id=None, drive=None, dynamic_show=False, tier = 'all', show_ids=False):
    
    if drive == None:
        system = 'local'    
    else:
        system = 'drive'
        
    """
        Lists "relative" paths to nested files and folders in a folder with path = folder_path
        Relative paths from the folder at folder_path
        
        A typical drive path must be like this :
            Folder1_title\Folder2_title\Folder3_title or file_title'
        if folder_path = Folder1_title
            relative paths are Folder2_title and Folder2_title\Folder3_title
            
        Input = {
                folder_path = path to folder on current system
                drive = the GoogleDrive drive object for listing paths in drive
                        = None for listing paths in local system
                dynamic_show = True prints each nested_path dynamically, False doesn't
                tier = 'all' returns all nested paths
                    = 'curr' returns contents immediately below current folder
                
        }
        
        Output = {returns a tuple of 3 elements : 
                the paths_list with the relative paths, 
                the list of ids of contents if used for GDrive (same as paths_list for drive = None) ,
                total_count = the number of 'non-folder' items in the folder at folder_path
        }
    """
        
    def list_all_contents_recur(folder_path, folder_id, paths_list, ids_list, file_count):
        
        #------------------------------------LOCAL---------------------------------------------
        if system == 'local':
            try:
                #if folder_path leads to a folder
                sub_folders = os.listdir(folder_path)
                if tier=='curr':
                    paths_list = sub_folders
                    if dynamic_show:
                        for count, i in enumerate(sub_folders):
                            if os.path.isdir(folder_path+'\\'+i):
                                ftype = 'D'
                            else:
                                ftype = 'F'
                            fsize = round(os.path.getsize(folder_path+'\\'+i)/1000, 2)
                            print(ftype+'[{}kB] {} : '.format(fsize, count+1) + i)
                            
                    return len(sub_folders)
            
            except NotADirectoryError:
                #if folder_path leads to a file
                fsize = round(os.path.getsize(folder_path)/1000, 2)
                if not folder_path == init_folder_path:
                    paths_list.append(folder_path.split(init_folder_path)[-1])
                else:
                    fname = re.split('[\\\\/]', init_folder_path)[-1]
                    paths_list.append(fname)
                if dynamic_show:
                    print('F[{}kB] : '.format(fsize) + paths_list[-1])
                
                return 1
            
            #If folder_path leads to empty folder
            if len(sub_folders) == 0:
                fsize = round(os.path.getsize(folder_path)/1000, 2)
                paths_list.append(folder_path.split(init_folder_path)[-1])
                if dynamic_show:
                    print('D[{}kB] : '.format(fsize) + paths_list[-1])
                
                return 0
            
            sub_folder_ids = sub_folders
        
        #--------------------------------------------DRIVE-------------------------------
        elif system == 'drive':
            file = drive.CreateFile({'id' : folder_id})
            file.FetchMetadata()
            
            if 'folder' in file['mimeType']:
                #if folder_path leads to a folder, list contents
                sub_folders_list = drive.ListFile({'q' : " '" + folder_id + "' in parents and trashed=false" }).GetList()
                sub_folders = [file['title'] for file in sub_folders_list]
                sub_folder_ids = [file['id'] for file in sub_folders_list]
                
                if tier=='curr':
                    paths_list = sub_folders
                    ids_list = sub_folder_ids
                    
                    if dynamic_show:
                        
                        if len(sub_folders)==0:
                            print("-- Empty folder --")
                        
                        else:
                            for count, i in enumerate(sub_folders):
                                if 'folder' in sub_folders_list[count]['mimeType']:
                                    ftype = 'D'
                                else:
                                    ftype = 'F'
                                fsize = round(float(sub_folders_list[count]['quotaBytesUsed'])/1000, 2)
                                if not show_ids:
                                    print_id = ''
                                else:
                                    print_id = sub_folder_ids[count]
                                    
                                print(print_id +" : "+ ftype+'[{}kB] {} : '.format(fsize, count+1) + i)
                            
                    return len(sub_folders)
                
            else:
                #if folder_path leads to a file
                if not init_folder_path == '':
                    if init_folder_id == folder_id:
                        paths_list.append(file['title'])
                    else:
                        paths_list.append(folder_path.split(init_folder_path)[-1])
                else:
                    paths_list.append(folder_path)
                
                if dynamic_show:
                    fsize = round(float(file['quotaBytesUsed'])/1000, 2)
                    
                    if not show_ids:
                        print_id = ''
                    else:
                        print_id = folder_id
                        
                    print(print_id +" : "+ 'F[{}kB] : '.format(fsize) + paths_list[-1])
                
                ids_list.append(folder_id)
                return 1
            
            #if folder_path leads to empy folder
            if len(sub_folders_list)==0:
                if not init_folder_path == '':
                    paths_list.append(folder_path.split(init_folder_path)[-1])
                else:
                    paths_list.append(folder_path)
                
                if dynamic_show:
                    
                    if not show_ids:
                        print_id = ''
                    else:
                        print_id = folder_id
                    
                    print(print_id +" : "+ 'D[0.0kB] : ' + paths_list[-1])
                    
                ids_list.append(folder_id)
                return 0
        
        #------------------------------------------Common---------------------------
        sub_folder_paths = [folder_path + '\\'+ p for p in sub_folders]
        
        for path, path_id in zip(sub_folder_paths, sub_folder_ids):
            file_count += list_all_contents_recur(path, path_id, paths_list, ids_list, 0)
        
        return file_count
    
    paths_list = []
    ids_list = []
    
    if system == 'local':
        init_folder_id = init_folder_path #if system is local
    
    else: #if system is drive
        if init_folder_id == None:
            try:
                list_path_ids = get_path_ids(init_folder_path, drive, create_missing_folders = False, path_to = 'folder')
                init_folder_id = list_path_ids[-1]
            except:
                list_path_ids = get_path_ids(init_folder_path, drive, create_missing_folders = False, path_to = 'not-folder')
                init_folder_id = list_path_ids[-1]
    
    total_count = list_all_contents_recur(init_folder_path, init_folder_id, paths_list, ids_list, 0)    
    
    return paths_list, ids_list, total_count


def upload_file_by_id(curr_file_path, drive_folder_id, drive, prompt='ask', file_count=1, total_count=1):
    
    """
    Uploads a file with current path = curr_file_path on system into
    a drive folder with id = drive_folder_id
    
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
        
    Input = {
            curr_file_path = path to file on current system
            drive_folder_id = id of drive folder into which upload will be done
            drive = GoogleDrive object
            prompt = 'ask' asks user to skip or overwrite if file already exists in drive
                    = 'skip' or 's' skips file if already exists
                    = 'overwrite' or 'o' overwrites the file if it already exists
                    = 'copy' creates an extra copy
            file_count = 1 (DEFAULT) to print the file's count when uploading folder
            total_count = 1 (DEFAULT) to print the total files in a folder when uploading
                    
    }
    Output = {
            Uploads the file into the drive folder with id = drive_folder_id
            returns None if no change in prompt,
            returns change in prompt from user otherwise
    }
    """
    file_name = re.split('[\\\\/]', curr_file_path)[-1]
    file_size = round(os.path.getsize(curr_file_path)/1000, 2)
    
    file = drive.CreateFile({'parents' : [{'id' : drive_folder_id}]})
    file['title'] = file_name
    print('Upload {}/{} '.format(file_count,total_count) + file_name + ' ({} kB):'.format(file_size), end='')
    file.SetContentFile(curr_file_path)    
    
    #Checking if file already exists :
    files_list = drive.ListFile({'q' : "title = '" + file_name + "' and '" + drive_folder_id + "' in parents and trashed=false"}).GetList()
    
    try:
        files_names = [f['title'] for f in files_list]
        match = files_names.index(file_name)
        drive_file_size = round(float(files_list[match]['quotaBytesUsed'])/1000, 2)
        print(' already ({} kB) exists : '.format(drive_file_size), end='')
        
        if prompt=='ask':
            prompt = input("Press 's' to skip / 'o' to overwrite / 'c' to create copy ('as'/'ao'/'ac' to repeat action for rest) : ")
            
            while not(prompt=='s' or prompt=='o' or prompt == 'c' or prompt=='as' or prompt=='ao' or prompt == 'ac'):
                prompt = input("Select 's' or 'o' or c: ")
                
        if prompt=='o' or prompt == 'ao' or prompt=='overwrite':
            file['id'] = files_list[match]['id']
            file.Upload()
            print('Overwritten')
            
        elif prompt=='s' or prompt == 'as' or prompt=='skip':
            print('skipped')
            
        if prompt=='copy' or prompt=='c' or prompt == 'ac':
            j = 0
            file_name_split = file_name.split('.')
            new_file_name = '.'.join(file_name_split[:-1]) + '({}).'.format(j) + file_name_split[-1]
            
            while new_file_name in files_names:
                j+=1
                new_file_name = '.'.join(file_name_split[:-1]) + '({}).'.format(j) + file_name_split[-1]
            
            file['title'] = new_file_name
            file.Upload()
            print('copy_created')
            
        
    except:
        file.Upload()
        print('Done!')
        
    if len(prompt)>1:
        return prompt[-1]
    else:
        return None


### This function is redundant ###------------------------------------------------------------------
def upload_file_by_path(curr_file_path, parent_folder_path, drive, empty_folder = False, create_missing_folders = True, prompt='ask'):
    
    """
    Uploads a file with current path = curr_file_path on system into
    a drive folder with path = parent_folder_path
    (This function is redundant - use upload_by_path() function)
    
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
        
    Input = {
            curr_file_path = path to file on current system
            parent_folder_path = id of drive folder into which upload will be done
            drive = GoogleDrive object
            empty-folder(boolean input) = False [DEFAULT] shows an error if the file is
                                                absent at curr_file_path
                    = True creates a path of folders till the parent folder of the file
                                    and leaves the last folder empty if file is absent
                                    at curr_file_path
            prompt = 'ask' asks user to skip or overwrite if file already exists in drive
                    = 'skip' or 's' skips file if already exists
                    = 'overwrite' or 'o' overwrites the file if it already exists
            
    }
    Output = {
            Uploads the file into the drive folder with path = parent_folder_path
            returns None if no change in prompt,
            returns change in prompt from user otherwise
    }
    """
    print('Use upload_by_path() instead of this. This function is obsolete.')
    path_id_list = get_path_ids(parent_folder_path, drive, create_missing_folders, path_to = 'folder')
    if os.path.exists(curr_file_path):
        prompt_chg = upload_file_by_id(curr_file_path, path_id_list[-1], drive, prompt=prompt)
        print('Done!')
    elif not empty_folder:
        raise FileNotFoundError(curr_file_path + ' doesnt exist.\n Try making the arguement empty_folder = True to keep the last folder empty at the end of the path : ' + parent_folder_path)
##This function is redundant#-----------------------------------------------------------

        
def upload(curr_path, drive_parent_folder_path, drive, prompt='ask'):
    
    """
    Uploads a folder/file at curr_path into the folder at drive_parent_folder_path
    Use drive_parent_folder_path = '' for uploading into the root folder
    
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
        
    Input = {
            curr_path = path to folder/file on current system
            drive_parent_folder_path = path to drive folder into which upload will be done
            drive = GoogleDrive object
            prompt = 'ask' asks user to skip or overwrite if file already exists in drive
                    = 'skip' or 's' skips file if already exists
                    = 'overwrite' or 'o' overwrites the file if it already exists
                    = 'copy' creates an extra copy
    }
    Output = {
            Just uploads the folder/file
    }
    """
    if not os.path.exists(curr_path):
        raise FileNotFoundError(curr_path + ' doesnt exist..')
    
    paths_list, _ ,  total_count = list_all_contents(curr_path)
    
    if len(paths_list)==1 and not paths_list[0][0] == '\\':
        #uploading single file :
        curr_folder_name = ''
    else:
        #uploading a folder    
        curr_folder_name = re.split('[\\\\/]', curr_path)[-1]
        
    count = 1
    print('\n')
    prompt_chg = None
    
    for path_i in paths_list:
        
        #change in prompt based on user input
        if prompt_chg:
            prompt = prompt_chg
        
        if drive_parent_folder_path == '' :
            drive_path = curr_folder_name + path_i
        else:
            drive_path = drive_parent_folder_path + '\\' + curr_folder_name +  path_i
            
        if os.path.isdir(curr_path + path_i):
            path_id = (get_path_ids(drive_path, drive, create_missing_folders = True, path_to = 'folder'))[-1]
        else:
            path_id_list = get_path_ids(drive_path, drive, create_missing_folders = True, path_to = 'not-folder')
            if len(path_id_list) == 1:
                path_id = 'root'
            else:
                path_id = path_id_list[-2]
            
            if curr_folder_name == '':
                #uploading single file
                prompt_chg = upload_file_by_id(curr_path, path_id, drive, file_count=count, total_count=total_count, prompt=prompt)
            else:
                #uploading file in a folder
                prompt_chg = upload_file_by_id(curr_path + path_i, path_id, drive, file_count=count, total_count=total_count, prompt=prompt)
            
            count += 1
        
    print('Done!')
    
def download_file_by_id(file_id, download_path, drive, prompt='ask',file_count=1, total_count=1):
    """
    Downloads a file at drive_path into the folder at download_path
    if file_id is known
    
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
        
    Input = {
            file_id = file's id in drive
            download_path = path to folder into which download will be done
            drive = GoogleDrive object
            prompt = 'ask' asks user to skip or overwrite if file already exists in drive
                    = 'skip' or 's' skips file if already exists
                    = 'overwrite' or 'o' overwrites the file if it already exists
                    = 'copy' creates an extra copy
            file_count = 1 (DEFAULT) to print the file's count when downloading folder
            total_count = 1 (DEFAULT) to print the total files in a folder when downloading        
    }
    Output = {
            Just downloads the file
            returns None if no change in prompt,
            returns change in prompt from user otherwise
    }
    """
    file = drive.CreateFile({ 'id' : file_id })
    file.FetchMetadata()
    file_name = file['title']
    file_size = round(float(file['quotaBytesUsed'])/1000, 2)
    print("Download {}/{} ".format(file_count,total_count) + file_name + ' ({} kB) : '.format(file_size), end='')
    
    new_file_path = download_path + '\\'+ file_name
    if os.path.exists(new_file_path):
        fsize = round(os.path.getsize(new_file_path)/1000, 2)
        print(' already ({} kB) exists : '.format(fsize), end='')
        
        if prompt=='ask':
            prompt = input("Press 's' to skip / 'o' to overwrite / 'c' to create copy ('as'/'ao'/'ac' to repeat action for rest) : ")
            
            while not(prompt=='s' or prompt=='o' or prompt=='c' or prompt=='as' or prompt=='ao' or prompt=='ac'):
                prompt = input("Select 's' or 'o' or 'c': ")    
            
        if prompt=='copy' or prompt=='c' or prompt=='ac':
            j = 0
            file_name_split = file_name.split('.')
            new_file_name = '.'.join(file_name_split[:-1]) + '({}).'.format(j) + file_name_split[-1]
            new_file_path = download_path + '\\' + new_file_name
            while os.path.exists(new_file_path):
                j+=1
                new_file_name = '.'.join(file_name_split[:-1]) + '({}).'.format(j) + file_name_split[-1]
                new_file_path = download_path + '\\' + new_file_name
            
            print('copy_create')
        
        elif prompt=='skip' or prompt=='s' or prompt=='as':
            print('skip')
        
        elif prompt=='overwrite' or prompt=='o'or prompt=='ao':
            print('overwrite')
            os.remove(download_path + '\\'+ file_name)
            
        file.GetContentFile(new_file_path)
    
    else:
        create_folders_path(download_path)
        file.GetContentFile(new_file_path)
        print('')
    
    if len(prompt)>1:
        return prompt[-1]
    else:
        return None
    
def download(drive, drive_path=None, drive_path_id=None, download_path=os.getcwd(), prompt='ask'):
    """
    Downloads a file/folder at drive_path into the folder at download_path
    Either id or path - one of them is sufficient
    
    A typical drive path must be like this :
        Folder1_title\Folder2_title\Folder3_title or file_title
        
    Input = {
            drive = GoogleDrive object
            drive_path = path to file/folder on drive
            drive_path_id = id of file/folder in drive
            download_path = path to folder into which download will be done
            prompt = 'ask' asks user to skip or overwrite if file already exists in drive
                    = 'skip' or 's' skips file if already exists
                    = 'overwrite' or 'o' overwrites the file if it already exists
                    = 'copy' creates an extra copy
    }
    Output = {
            Just downloads the folder/file and returns None
    }
    """
    print("Fetching ids_list : ",end='')
    if drive_path==None and drive_path_id != None:
        drive_path, _ = get_path_from_id(drive, drive_path_id)
            
    paths_list, ids_list, total_count = list_all_contents(drive_path, drive_path_id, drive=drive, dynamic_show=False, tier = 'all')
    count = 1
    print("{} paths found ...".format(total_count))
    
    #if drive_path leads to a file
    if len(paths_list)==1 and not (paths_list[0][0] == '\\' and paths_list[0][0] == '/'):
        prompt_chg = download_file_by_id(ids_list[0], download_path, drive, prompt=prompt)
        print("Done!")
        return 
    
    prompt_chg = None
    #if drive_path leads to folder
    for path_i, id_i in zip(paths_list, ids_list):
        
        #change in prompt based on user input
        if prompt_chg:
            prompt = prompt_chg
        
        path_i = '\\' + re.split('[\\\\/]', drive_path)[-1] + path_i
        
        file = drive.CreateFile({'id' : id_i})
        file.FetchMetadata()
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            create_folders_path(download_path + path_i)
            count+=1
        else:
            folder_path = '\\'.join(re.split('[\\\\/]', path_i)[:-1])
            prompt_chg = download_file_by_id(id_i, download_path + folder_path, drive, prompt=prompt, file_count=count, total_count=total_count)
            count+=1
    
    print("Done!")
    
    
    