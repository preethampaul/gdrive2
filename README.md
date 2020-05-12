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
