# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 13:21:48 2020
@author: Preetham
"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import gd.util

gauth = GoogleAuth()
util.auth_from_cred(gauth)
#gauth consists of information for authentication

drive = GoogleDrive(gauth)
