# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 13:21:48 2020
@author: Preetham
"""

import os
import re
from time import sleep
from datetime import date

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import util

gauth = GoogleAuth()
util.auth_from_cred(gauth)
#gauth consists of information for authentication

drive = GoogleDrive(gauth)
#This object is used to push or access file from the drive,
#whose access information is stored in gauth

##############################################
#Copy the above lines of code for using the google API

#Use for folder upload
#util.upload_folder_by_path(current_folder, drive_folder, drive) function
#to upload a folder

#Use for file upload
#util.upload_file_by_path(curr_file_path, parent_folder_path, drive)

#BEWARE OF FILE OVERWRITING : make sure file names dont match

################################################