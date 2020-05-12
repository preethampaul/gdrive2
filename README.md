# **gdrive**
## File management for Google Drive using python

gdrive is inspired from git's push-pull functionalities from command line. With gdrive, some command line functions like `cd` and `ls` can be used to view files in drive folders directly from command line.

### Requirements
PyDrive library is required for this :
To install Pydrive :
for PIP : use command

```pip install PyDrive```

for ANACONDA : use command
```conda install -c conda-forge pydrive```

**NOTE:**
A client secrets file is required. Read [pydrive's documentation](https://pythonhosted.org/PyDrive/quickstart.html)

___
The following files are ESSENTIAL for the Google API to work :

Files containing utility functions in util folder:
1. api_auth_util.py
2. drive_util.py

Files containing client data or in simple terms, the app's data which modifies data in the GDrive in api_data folder: 
1. client_secrets.json
2. settings.yaml

___
The following files are EXAMPLE files which have few lines of code for guidance:
1. main.py --> This file contains code which has to be copied to the application which uploads files to Gdrive.
				If the main.py file is run, it creates the creds.txt file (mentioned below), which is
				important for authentication. So, another way is one can first run the main.py file, and then
				use the utility functions in their applications to upload files. But still even in the latter
				way, one has to copy contents of main.py to their application to use the utility function.

2. GoogleDriveFile_example.txt --> This is just an example of how a typical GoogleDriveFile object looks
				A GoogleDriveFile is the object which encodes all metadata for every file in GDrive
				Its interesting to go through this and see what all metadata GDrive records when a file is uploaded
___
The following files get CREATED:

Files containing Authentication data about the GDrive being modified:
**WARNING : ANYONE WITH THIS FILE CAN ACCESS THE GDRIVE FILE, SO NEVER SHARE THIS FILE!!**
**IT GETS CREATED IF THE APP IS RUN FOR THE FIRST TIME, SO THE USER CAN AUTHENTICATE THE FIRST TIME**
**AND ONCE AUTHENTICATION IS DONE, THE APP CAN ENDLESSLY ACCESS THE GDRIVE**
1. creds.txt

Note : To change the GDrive to modify, just delete this file and run the main.py or a file with contents of main.py
copied to it.

___
CHANGING SCOPE OF ACCESS IN GDRIVE :
The app can currently can change ALL files in the Gdrive once authentications is done. This is because
in 'settings.yaml' file, one can find something like this as default.
```
oauth_scope:
  - https://www.googleapis.com/auth/drive
  - https://www.googleapis.com/auth/drive.install
```
This can be changed to the following, to allow the functions to be able to modify only those folders which are
created by these functions. After changing this in settings.yaml, one has to delete 'creds.txt' and re-authenticate
to see the effect.
```
oauth_scope:
  - https://www.googleapis.com/auth/drive.file
  - https://www.googleapis.com/auth/drive.install
```
See https://developers.google.com/identity/protocols/googlescopes#drivev3 for other scopes.
___
The two main functions from drive_util.py which are of interest (read documentation for details):
(These are called after copying the contents of main.py into the application and run)

#Uploading a file : 
util.upload_file_by_path(curr_file_path, drive_parent_folder_path, drive)

#Uploading a folder :
util.upload_folder_by_path(curr_folder_path, drive_parent_folder_path, drive)

A typical drive path must be like this :
        'Folder1_in_the_Gdrive_root_title\Folder2_title\Folder3_title or file_title'

** WARNING : curr_file_path must not include the path to the current working directory !!**
** WARNING : If one tries to upload a file which has the name of a file which is already present in drive_parent_folder_path,**
			the latter file is OVERWRITTEN !!**







