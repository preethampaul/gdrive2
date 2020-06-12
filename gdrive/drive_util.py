#This file contains functions relevant to handling files
#in the google drive

import os
import re
from apiclient import errors
import numpy as np

#when my drive is the current drive
DEFAULT_ROOT = 'root'

def isdir(drive, file_id):
    """
    checks if the file with file_id is a directory.
    
    Parameters
    -----------------
    drive : pydrive.GoogleDrive() object
    file_id : string
        The file_id of file whose mimeType is to be checked
        
    Returns
    ----------------
    Whether dir. or not : bool
        True if it is a directory/folder
        
    """
    file = drive.CreateFile({'id' : file_id})
    fetchMetadata(file, fields="mimeType")
    
    if 'folder' in file['mimeType']:
        return True
    else:
        return False


def query_to_paths(drive, query, path, path_id=None, tier='all', default_root=DEFAULT_ROOT):
    """
    Used in gdrive.find function to obtain paths from queries.
    
    A query includes glob patterns connected by 'and' and/or 'or' operators
    
    Parameters
    -----------
    drive : pydrive.GoogleDrive() object
    query : string
        query to search for a file in specified path
    path : string
        directory path in drive where the query is applied and files are searched.
        All paths queried will be relative to this
    path_id : string (optional)
        id of the directory path
    tier : string or int
        The tier in the hierarchy of files
    default_root : string (optional)
        The id of the drive.    
    

    Notes
    -----------
    If tier = 'all', all tiers are searched (optional)
    
    If tier = 'curr', only immediate children are searched
    
    If integer passed, search will be done upto that tier.
    
    For example, tier = 1 is same as tier = 'curr'
    

    Returns
    -----------
    paths and path_ids satisfying the query : tuple
        (paths, path_ids)
    
    """
    file_type = None
    
    if query.startswith('%f '):
        file_type = 'f'
        query.strip('%f ')
    
    elif query.startswith('%d '):
        file_type = 'd'
        query.strip('%d ')
    
    cond_list = re.split(r"(\Wand\W|\Wor\W)+" ,query)
    path_ind_list = cond_list
    
    #Listing all paths
    (paths_list, ids_list, count) = list_all_contents(path, init_folder_id=path_id, drive=drive, dynamic_show=False, tier=tier, default_root=default_root)
    
    i = 0
    is_not = False #if not is present
    while i<len(cond_list):
        
        if cond_list[i] == ' and ' or cond_list[i] == ' or ':
            i+=1
            continue
        
        file_cond = cond_list[i]
        path_ind_list[i] = []
        
        #checks if not is present
        if file_cond.startswith('not '):
            file_cond = file_cond.partition('not ')[-1]
            is_not = True
        
        if "\"" in file_cond or "'" in file_cond:
            file_cond = re.split("\"|\'", file_cond)[1]
        else:
            file_cond = re.split("\"|\'", file_cond)[0]
        
        #full match
        if not '*' in file_cond:
            for j in range(len(paths_list)):
                if ((not is_not) and file_cond == paths_list[j]) or (is_not and not file_cond == paths_list[j]):
                    path_ind_list[i] += [j]

            i += 1
            is_not = False
            continue
        
        #partial matches using *
        q_path_list = paths_list.copy()
        path_ind_list[i] = list(range(len(paths_list)))
        
        #delimiters attached by *
        delims = re.split('\*', file_cond)
        for delim_i in range(len(delims)):
            if delims[delim_i] == '':
                continue
            
            q_path_len = len(q_path_list)
            j = 0
            while j < q_path_len:
                path_j = q_path_list[j]
                parted_q_path = path_j.partition(delims[delim_i])
                
                if not (delims[delim_i] == parted_q_path[1] and parted_q_path[-1] == ''):
                    q_path_list[j] = parted_q_path[-1]
                    
                if not file_cond.startswith('*') and not parted_q_path[0] == '':
                    q_path_list[j] = ''
                
                if not file_cond.endswith('*') and not parted_q_path[-1] == '':
                    q_path_list[j] = ''
                
                if q_path_list[j] == '':
                    _ = q_path_list.pop(j)
                    _ = path_ind_list[i].pop(j)
                    q_path_len -= 1
                    continue
                
                j+=1
        
        if is_not:
            path_ind_list[i] = list(np.array(range(len(paths_list)))[[not (ind in path_ind_list[i]) for ind in range(len(paths_list))]])
            is_not = False
            
        #while loop for connecting strings connected by and/or operators
        i+=1
    
    #logic operation
    op = None
    op_list = np.array([])
    
    for ii in path_ind_list:
        if type(ii) == str:
            op = ii
            continue
        
        if len(op_list)==0:
            op_list = np.array(ii)
            continue
        
        if 'and' in op:
            op_list = op_list[ [ind in ii for ind in op_list] ]
        
        elif 'or' in op:
            op_list = np.unique(np.concatenate((op_list, ii)))
            
        op = None
    
    if len(op_list)==0:
        return ([], [])
    
    #updating paths_list and ids_list
    paths_list = list(np.array(paths_list)[op_list])
    ids_list = list(np.array(ids_list)[op_list])
    
    if file_type==None:
        return (paths_list, ids_list)
    
    #Now checking for the required file type
    count = 0
    list_len = len(ids_list)
    remove_id = False
    
    while count<list_len:
        file_id = ids_list[count]
        if isdir(drive, file_id):
            if file_type == 'f':
                remove_id = True
        else:
            if file_type == 'd':
                remove_id = True
        
        if remove_id:
            _ = ids_list.pop(count)
            _ = paths_list.pop(count)
            remove_id = False
            list_len = len(ids_list)
            continue
        
        count+=1
    
    return (paths_list, ids_list)
    
    

def parse_drive_path(path, drive, parent_id, default_root=DEFAULT_ROOT):
    """
    Parses path into an absolute drive path
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
    
    Parameters
    -------------
    path : string
        drive path to be parsed
    drive : pydrive.GoogleDrive() object
    parent_id : string
        parent id required to parse relative paths
    default_root : string (optional)
        id of the drive

    Returns
    --------------
    parsed drive path : string

    """
    
    if "'" in path or "\"" in path:
        path = path[1:-1]
        
    path_list = re.split("[\\\\/]", path)
    init_len = len(path_list)
    
    parent_id_i = parent_id    
    char = path_list[0]
    
    while char == '~' or char == '..':
        
        #Home relative paths
        if char == '~':
            parent_id_i = default_root
            path_list.remove('~')
            
        #parent relative paths
        elif char == '..':
            _, ids_list = get_path_from_id(drive, parent_id_i, default_root=default_root)
            
            if len(ids_list)>1:
                parent_id_i = ids_list[-2]
            else:
                parent_id_i = ids_list[-1]
                
            path_list.remove('..')
        
        if len(path_list)>0:
            char = path_list[0]
        else:
            break
    
    base_path, _ = get_path_from_id(drive, parent_id_i, default_root=default_root)
        
    if len(path_list)==0:
        return base_path
    
    #relative paths
    if path_list[0] == '' and len(path_list)>1:
        new_path = base_path + '/'.join(path_list)
        return new_path
    
    if len(path_list) == init_len:
        return path
    
    if base_path=='':
        return '/'.join(path_list)
    else:
        return base_path + '/' + '/'.join(path_list)


def fetchMetadata(drive_file, fields=None):
    """
    A replica of FetchMetadata() from GoogleDriveFile class of pyDrive 1.3.1
    Changes made : replaced 'supportsTeamDrives' with 'supportsAllDrive'

    Parameters
    -------------
    drive_file : pydrive.GoogleDriveFile() object
    fields : string (optional)
        If metadata about a specific field is required, pass it here as querry string. 
        For example : fields = "field1,field2,field3"

    Returns
    -------------
    None
        Updates drive_file with metadata.    
    """

    if fields==None:
        fields = drive_file._ALL_FIELDS
    
    file_id = drive_file.metadata.get('id') or drive_file.get('id')
    
    if file_id:
      try:
        metadata = drive_file.auth.service.files().get(
          fileId=file_id,
          fields=fields,
          # Support All drives -- Changed this
          supportsAllDrives=True
        ).execute(http=drive_file.http)
        
      except errors.HttpError as error:
        reason = error._get_reason
        print(str(reason))
      
      else:
        drive_file.uploaded = True
        drive_file.UpdateMetadata(metadata)
    
    else:
      print("FileNotUploadedError()")
      

def create_folders_path(path):
    """
    Creates non-existing folders along the local system path
    
    Parameters
    ------------
    path : string
        path to a folder
            
    Returns
    ------------
    None
        Creates folders in the local system

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
    
    Parameters
    ------------
    folder_name : string
        name of folder
    parent_folder_id : string
        ID of the parent folder
    drive : pydrive.GoogleDrive() object
    
    Returns
    ------------
    id of the created folder : string

    """
    
    folder = drive.CreateFile({'parents' : [{'id' : parent_folder_id}],'mimeType' : 'application/vnd.google-apps.folder', 'title' : folder_name})
    folder.Upload(param={'supportsAllDrives' : True})
    return folder['id']

def get_path_from_id(drive, file_id, default_root=DEFAULT_ROOT):
    """
    Returns drive path of file with specified id.
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
    
    Parameters
    -------------
    drive : pydrive.GoogleDrive() object
    file_id : string
        id of file whose path is required
    default_root : string (optional)
        id of the drive

    Returns
    -------------
    path to file or folder : tuple
        (string of path, list of ids leading up to file_id)

    """


    path = []
    ids = []
    
    actual_root = drive.CreateFile({'id' : default_root})
    fetchMetadata(actual_root, fields="id")
    
    while file_id!=actual_root['id']:
        file = drive.CreateFile({'id' : file_id})
        fetchMetadata(file)
        path.append(file['title'])
        ids.append(file_id)
        
        if len(file['parents'])==0:
            break
        
        file_id = file['parents'][0]['id']
        
    ids.append(default_root)
    if "My Drive" in path:
        path.remove("My Drive")
    
    return '/'.join(path[::-1]), ids[::-1]


def get_id_by_name(name, parent_folder_id, drive, file_type = 'all'):
    
    """
    Returns list of ids for folders or files with title = name in the drive folder
    with id = parent_folder_id
    

    Parameters
    --------------
    name : string
        name of folder or file
    parent_folder_id : string
        ID of the parent folder
    drive : pydrive.GoogleDrive() object
    file_type : string (optional)
    

    Notes
    --------------
    For file_type, use one of the following:
        
        'folder' to return only folders' ids
        
        'not-folder' to return ids other than folders
        
        'all' to return all ids with the name (default)
    

    Returns
    --------------
    ids and mime types : tuple
        a tuple of 2 lists : (list of ids, list of corresponding mime types)
    
    """
    
    try:
        file_list = drive.ListFile({'q' : "title = '" + name + "' and '" + parent_folder_id + "' in parents and trashed=false",
                                    'supportsAllDrives' : "true",
                                    'corpora' : "allDrives",
                                    'includeItemsFromAllDrives' : "true"
                                    }).GetList()
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


def get_path_ids(drive_path, drive, create_missing_folders = True, relative_id = None, path_to = 'folder', default_root=DEFAULT_ROOT):
    
    """
    Returns list of ids for folders or files in the path to the drive_path
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
    
    The last id in this list will be of a folder or a file, which the user must determine
    with the path_to arguement
    

    Parameters
    -------------

    drive_path : string
        path to a file or folder in drive
    
    drive : pydrive.GoogleDrive() object
    
    create_missing_folders : bool (optional)
        
        True if create the folders in the path if they dont exist
        
        False returns a error if any of the folder in the path doesnt exist
    
    relative_id : None or string (optional)
        None if absolute paths are desired and <current working folder id> if relative paths are desired
    
    path_to : string (optional)
    
        'folder' to return only folders' ids (default)
        
        'not-folder' to return ids other than folders
    

    Returns
    -------------
    path_ids : list
        returns a list of all ids in the path like this -
            
            [Folder1_id, Folder2_id, Folder3_id] if path_to = 'folder'
            
            [Folder1_id, Folder2_id, File id] if path_to = 'not-folder'
            
            [Folder1_id, Folder2_id, 'no-file-found'] if path_to = 'not-folder' and the file at the end of path doesnt exist
        
        Gives error if there are more than one files or more than folders with same name

    """
    #For root path
    if drive_path == '':
        if not relative_id==None:
            return [relative_id]
        else:
            return [default_root]
    
    path_list = re.split('[\\\\/]', drive_path)
    path_id_list = path_list
    
    for i in range(len(path_list)):
        
        if i == 0:
            if relative_id == None:
                parent_folder_id = default_root
            else:
                parent_folder_id = relative_id
        else:
            parent_folder_id = path_id_list[i-1]
        
        if i < len(path_list) - 1:
            path_id, _ = get_id_by_name(path_list[i], parent_folder_id, drive, file_type = 'folder')
        else:
            path_id, _ = get_id_by_name(path_list[i], parent_folder_id, drive, file_type = path_to)
        
        if len(path_id) > 1:
            raise NameError('More than one folder or file found with the same name : '+ path_list[i] +' in ' + '/'.join(path_list[:i]))
        
        elif len(path_id) == 0:
            
            if i == len(path_list) - 1 and path_to == 'not-folder':
                path_id_list[i] = 'no-file-found'
                    
            elif create_missing_folders:
                path_id_list[i] = create_folder(path_list[i], parent_folder_id, drive)
            
            else:
                raise ValueError("path to file-type: '" + path_to +"' not found with name : "+ path_list[i] +" in '" + '/'.join(path_list[:i]) + "'")
        
        else:
            path_id_list[i] = path_id[0]
        
    return path_id_list
 
    
def list_all_contents(init_folder_path, init_folder_id=None, drive=None,
                      dynamic_show=False, tier = 'all', show_ids=False, 
                      get_types = False, default_root=DEFAULT_ROOT):
        
    """
    Lists "relative" paths to nested files and folders in a folder with path = folder_path
    Relative paths from the folder at init_folder_path
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
    
    For example : if init_folder_path = Folder1_title
        relative paths are Folder2_title and Folder2_title/Folder3_title
    
    If a file is present at init_folder_path, just returns the file_name and id


    Parameters
    ---------------
    init_folder_path : string
        path to folder on current system
    
    init_folder_id : string or None (optional)
        
        id of the folder at init_folder_path
        
        Only one of init_folder_path and init_folder_id is sufficient
        
        None if unknown, but init_folder_path is known
    
    drive : pydrive.GoogleDrive() drive object or None (optional)
        None for listing paths in local system; otherwise, lists paths in drive
    
    dynamic_show : bool (optional)
        if True, prints each nested_path dynamically, False doesn't
    
    tier : string or int(optional)
        'all' returns all nested paths
        
        'curr' returns contents immediately below current folder
        
        If int, tier should be the number of tiers in hierarchy of nested files to list.
        For example, tier = 1 is same as tier == 'curr'
        
        Interger-type tier works only for system = 'drive'
    
    show_ids : bool (optional)
        If True, prints ids along with file names when dynamic_show = True
    
    get_types : bool (optional)
        If True, even the file types are returned as in the tuple and works
    
    default_root : string (optional)
        id of the drive


    Returns
    ---------------
    contnets of the folder : tuple
        a tuple of 3 **(or 4)** elements
            (the paths_list with the relative paths, 
            the list of ids of contents if used for GDrive (same as paths_list for drive = None),
            **the list of file_types (included only if get_types = True),**
            total_count = the number of 'non-folder' items in the folder at folder_path)
        

    """

    #To specify to look in local system or in drive
    if drive == None:
        system = 'local'    
    else:
        system = 'drive'  

    def list_all_contents_recur(folder_path, folder_id, paths_list, ids_list, type_list, file_count, tier):
        
        #if tiers end
        if tier==0:
            return 0
        
        #------------------------------------LOCAL---------------------------------------------
        if system == 'local':
            try:
                #if folder_path leads to a folder
                sub_folders = os.listdir(folder_path)
                if tier=='curr':
                    paths_list+=sub_folders
                    
                    for count, i in enumerate(sub_folders):
                        if os.path.isdir(folder_path+'\\'+i):
                            ftype = 'D'
                        else:
                            ftype = 'F'
                        
                        type_list+=[ftype]
                        if dynamic_show:
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
                
                type_list += ['F']
                if dynamic_show:
                    print('F[{}kB] : '.format(fsize) + paths_list[-1])
                
                return 1
            
            #If folder_path leads to empty folder
            if len(sub_folders) == 0:
                fsize = round(os.path.getsize(folder_path)/1000, 2)
                paths_list.append(folder_path.split(init_folder_path)[-1])
                
                type_list += ['D']
                
                if dynamic_show:
                    print('D[{}kB] : '.format(fsize) + paths_list[-1])
                
                return 0
            
            sub_folder_ids = sub_folders
        
        #--------------------------------------------DRIVE-------------------------------
        elif system == 'drive':
            file = drive.CreateFile({'id' : folder_id})
            fetchMetadata(file)
            
            if 'folder' in file['mimeType']:
                #if folder_path leads to a folder, list contents
                sub_folders_list = drive.ListFile({'q' : " '" + folder_id + "' in parents and trashed=false",
                                                   'supportsAllDrives' : "true",
                                                   'corpora' : "allDrives",
                                                   'includeItemsFromAllDrives' : "true"
                                                   }).GetList()
                sub_folders = [file['title'] for file in sub_folders_list]
                sub_folder_ids = [file['id'] for file in sub_folders_list]
                sub_types = [file['mimeType'] for file in sub_folders_list]
                
                if tier=='curr' or tier==1:
                    
                    if tier=='curr':
                        paths_list += sub_folders
                        
                    elif tier == 1:
                        paths_list += [folder_path + '/' + i for i in sub_folders]
                    
                    ids_list+=sub_folder_ids
                    type_list += sub_types

                    if dynamic_show:
                        
                        if len(sub_folders)==0:
                            print("-- Empty folder --")
                        
                        else:
                            for count, i in enumerate(sub_folders):
                                if 'folder' in sub_types[count]:
                                    ftype = 'D'
                                else:
                                    ftype = 'F'
                                fsize = round(float(sub_folders_list[count]['quotaBytesUsed'])/1000, 2)
                                if not show_ids:
                                    print_id = ''
                                else:
                                    print_id = sub_folder_ids[count]
                                    
                                print(print_id +" : "+ ftype+'[{}kB] {} : '.format(fsize, count+1) + i)
                    
                    if tier=='curr':
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
                type_list.append(file['mimeType'])
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
                type_list.append(file['mimeType'])
                return 0
        
        #------------------------------------------Common for both drive and Local---------------------------
        sub_folder_paths = [folder_path + '/'+ p for p in sub_folders]
        
        for path, path_id in zip(sub_folder_paths, sub_folder_ids):
            if type(tier)==int:
                file_count += list_all_contents_recur(path, path_id, paths_list, ids_list, type_list, 0, tier-1)
            else:
                file_count += list_all_contents_recur(path, path_id, paths_list, ids_list, type_list, 0, tier)
        
        return file_count
    
    paths_list = []
    ids_list = []
    type_list = []
    
    if system == 'local':
        init_folder_id = init_folder_path #if system is local
    
    else: #if system is drive
        if init_folder_id == None:
            try:
                list_path_ids = get_path_ids(init_folder_path, drive, create_missing_folders = False, path_to = 'folder', default_root=default_root)
                init_folder_id = list_path_ids[-1]
            except:
                list_path_ids = get_path_ids(init_folder_path, drive, create_missing_folders = False, path_to = 'not-folder', default_root=default_root)
                init_folder_id = list_path_ids[-1]
                
    total_count = list_all_contents_recur(init_folder_path, init_folder_id, paths_list, ids_list, type_list, 0, tier)    
    
    if get_types:
        return paths_list, ids_list, type_list, total_count
    else:
        return paths_list, ids_list, total_count


def upload_file_by_id(curr_file_path, drive_folder_id, drive, prompt='ask', file_count=1, total_count=1):
    
    """
    Uploads a file with current path = curr_file_path on system into
    a drive folder with id = drive_folder_id
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
        

    Parameters
    --------------
    curr_file_path : string
        path to file on current system
    drive_folder_id : string
        id of drive folder into which upload will be done
    drive : pydrive.GoogleDrive() object
    prompt : string (optional)
    file_count : int (optional)
        1 (default) to print the file's count when uploading folder
    total_count : int (optional)
        1 (DEFAULT) to print the total files in a folder when uploading
         

    Notes:
    ------------
    For prompt, use the following:
        
        'ask' asks user to skip or overwrite if file already exists in drive (default)
        
        'skip' or 's' skips file if already exists
        
        'overwrite' or 'o' overwrites the file if it already exists
        
        'copy' creates an extra copy
    

    Returns
    -------------
    multiple outputs : None or string
        
        Uploads the file into the drive folder with id = drive_folder_id
        
        returns None if no change in prompt,
        
        returns change in prompt from user otherwise
    
    """
    file_name = re.split('[\\\\/]', curr_file_path)[-1]
    file_size = round(os.path.getsize(curr_file_path)/1000, 2)
    
    file = drive.CreateFile({'parents' : [{'id' : drive_folder_id}]})
    file['title'] = file_name
    print('Upload {}/{} '.format(file_count,total_count) + file_name + ' ({} kB):'.format(file_size), end='')
    file.SetContentFile(curr_file_path)    
    
    #Checking if file already exists :
    files_list = drive.ListFile({'q' : "title = '" + file_name + "' and '" + drive_folder_id + "' in parents and trashed=false",
                                 'supportsAllDrives' : "true",
                                 'corpora' : "allDrives",
                                 'includeItemsFromAllDrives' : "true"
                                 }).GetList()
    
    try:
        files_names = [f['title'] for f in files_list]
        match = files_names.index(file_name)
        drive_file_size = round(float(files_list[match]['quotaBytesUsed'])/1000, 2)
        print(' already ({} kB) exists : \n'.format(drive_file_size), end='')
        
        if prompt=='ask':
            prompt = input("Press 's' to skip / 'o' to overwrite / 'c' to create copy ('as'/'ao'/'ac' to repeat action for rest) : ")
            
            while not(prompt=='s' or prompt=='o' or prompt == 'c' or prompt=='as' or prompt=='ao' or prompt == 'ac'):
                prompt = input("Select 's' or 'o' or c: ")
                
        if prompt=='o' or prompt == 'ao' or prompt=='overwrite':
            file['id'] = files_list[match]['id']
            file.Upload(param={'supportsAllDrives' : True})
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
            file.Upload(param={'supportsAllDrives' : True})
            print('copy_created')
            
        
    except:
        file.Upload(param={'supportsAllDrives' : True})
        print('Done!')
        
    if len(prompt)>1:
        return prompt[-1]
    else:
        return None

        
def upload(curr_path, drive_parent_folder_path, drive, prompt='ask', default_root=DEFAULT_ROOT):
    
    """
    Uploads a folder/file at curr_path into the folder at drive_parent_folder_path
    Use drive_parent_folder_path = '' for uploading into the root folder
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
        

    Parameters
    ---------------
    curr_path : string
        path to folder or file on current system
    drive_parent_folder_path : string
        path to drive folder into which upload will be done
    drive : pydrive.GoogleDrive() object
    prompt : string (optional)
    

    Notes:
    ------------
    For prompt, use the following:
        
        'ask' asks user to skip or overwrite if file already exists in drive (default)
        
        'skip' or 's' skips file if already exists
        
        'overwrite' or 'o' overwrites the file if it already exists
        
        'copy' creates an extra copy
    

    Returns
    ---------------
    None
        Just uploads the folder or file
    
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
            drive_path = drive_parent_folder_path + '/' + curr_folder_name +  path_i
            
        if os.path.isdir(curr_path + path_i):
            path_id = (get_path_ids(drive_path, drive, create_missing_folders = True, path_to = 'folder'))[-1]
        else:
            path_id_list = get_path_ids(drive_path, drive, create_missing_folders = True, path_to = 'not-folder')
            if len(path_id_list) == 1:
                path_id = default_root
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
        Folder1_title/Folder2_title/Folder3_title or file_title
        

    Parameters
    ----------------
    file_id : string
        file's id in drive
    download_path : string
        path to folder into which download will be done
    drive : pydrive.GoogleDrive() object
    prompt : string (optional)
    file_count : int (optional)
        1 (default) to print the file's count when downloading folder
    total_count : int (optional)
        1 (default) to print the total files in a folder when downloading        
    

    Notes:
    ------------
    For prompt, use the following:
        
        'ask' asks user to skip or overwrite if file already exists in drive (default)
        
        'skip' or 's' skips file if already exists
        
        'overwrite' or 'o' overwrites the file if it already exists
        
        'copy' creates an extra copy
    

    Returns
    ----------------
    multiple outputs : None or string
        Just downloads the file
        returns None if no change in prompt,
        returns change in prompt from user otherwise
    
    """
    file = drive.CreateFile({ 'id' : file_id })
    fetchMetadata(file)
    file_name = file['title']
    file_size = round(float(file['quotaBytesUsed'])/1000, 2)
    print("Download {}/{} ".format(file_count,total_count) + file_name + ' ({} kB) : '.format(file_size), end='')
    
    new_file_path = download_path + '\\'+ file_name
    if os.path.exists(new_file_path):
        fsize = round(os.path.getsize(new_file_path)/1000, 2)
        print(' already ({} kB) exists :\n'.format(fsize), end='')
        
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

    
def download(drive, drive_path=None, drive_path_id=None, download_path=os.getcwd(), prompt='ask', default_root=DEFAULT_ROOT):
    """
    Downloads a file or folder at drive_path into the folder at download_path
    Either id or path - one of them is sufficient
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
        

    Parameters
    -----------------
    drive : pydrive.GoogleDrive() object
    
    drive_path : string or None
        path to file/folder on drive (None is default)
    
    drive_path_id : string or None
        id of file/folder in drive.
        
        Either the drive path o the drive_path_id is sufficient (None is default)
    
    download_path : string (optional)
        path to folder into which download will be done
        
        current_working directory is default
    
    prompt : string (optional)
    

    Notes:
    ------------
    For prompt, use the following:
        
        'ask' asks user to skip or overwrite if file already exists in drive (default)
        
        'skip' or 's' skips file if already exists
        
        'overwrite' or 'o' overwrites the file if it already exists
        
        'copy' creates an extra copy
    

    Returns
    -----------------
    None
        Just downloads the folder or file and returns None
    
    """
    print("Fetching ids_list : ",end='')
    
    paths_list, ids_list, total_count = list_all_contents(drive_path, drive_path_id, drive=drive, dynamic_show=False, tier = 'all', default_root=default_root)
    
    if drive_path==None and drive_path_id != None:
        drive_path, _ = get_path_from_id(drive, drive_path_id)
    
    count = 1
    print("{} paths found ...".format(total_count))
    
    #if drive_path leads to a file
    if len(paths_list)==1 and not (paths_list[0][0] == '\\' and paths_list[0][0] == '/'):
        prompt_chg = download_file_by_id(ids_list[0], download_path, drive, prompt=prompt)
        print("Done!\n------------\n")
        return 
    
    prompt_chg = None
    #if drive_path leads to folder
    for path_i, id_i in zip(paths_list, ids_list):
        
        #change in prompt based on user input
        if prompt_chg:
            prompt = prompt_chg
        
        path_i = '\\' + re.split('[\\\\/]', drive_path)[-1] + path_i
        
        file = drive.CreateFile({'id' : id_i})
        fetchMetadata(file)
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            create_folders_path(download_path + path_i)
            count+=1
        else:
            folder_path = '\\'.join(re.split('[\\\\/]', path_i)[:-1])
            prompt_chg = download_file_by_id(id_i, download_path + folder_path, drive, prompt=prompt, file_count=count, total_count=total_count)
            count+=1
    
    print("Done!")
    

def delete(drive, drive_path=None, drive_path_id=None, relative_id=None, hard_delete=False, default_root=DEFAULT_ROOT):
    """
    deletes a file or folder using the drive_path or the drive_path_id.
    
    A typical drive path must be like this :
        Folder1_title/Folder2_title/Folder3_title or file_title
    

    Parameters
    ---------------
    drive : pydrive.GoogleDrive() object
    
    drive_path : stringor None
        path to the file or folder in drive to be deleted
    
    drive_path_id : string or None
        id of the folder or file to be deleted.
        
        Only one of drive_path and drive_path_id is sufficient.
    
    relative_id : None or string (optional)
        None if absolute paths are desired (default) and <current working folder id> if relative paths are desired
    
    hard_delete : bool (optional)
        If False, files are moved to trash (default)
        
        If True, files are deleted permanently
    
    default_root : string (optional)
        id of the drive
    

    Returns
    --------------
    None
        Deletes the specified files or folders
    """
    if drive_path_id==None and drive_path != None:
        try:
            drive_path_id = get_path_ids(drive_path, drive, create_missing_folders = False, relative_id = relative_id, path_to = 'folder', default_root=DEFAULT_ROOT)[-1]
        except:
            drive_path_id = get_path_ids(drive_path, drive, create_missing_folders = False, relative_id = relative_id, path_to = 'not-folder', default_root=DEFAULT_ROOT)[-1]
    
    if drive_path_id == 'no-file-found':
        print("The file doesn't exists.")
        return
    
    file = drive.CreateFile({'id' : drive_path_id})
    fetchMetadata(file)
    
    if hard_delete:
        file.Delete(param={'supportsAllDrives' : True})
    else:
        file.Trash(param={'supportsAllDrives' : True})
        
