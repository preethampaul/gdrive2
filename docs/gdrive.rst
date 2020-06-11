gdrive Functions and Commands
==============

The following submodules are present in the package:
::

   gdrive
   |_______gd
   |_______drive_util
   |_______auth_util
   |_______paths

The main module that is automatically imported when gdrive is imported is **gdrive.gd**.Other modules are utility modules, whose functions are used in **gd**. **paths** module only contains file paths which are imported as constants in other modules.

gdrive.gd module
####################

This module need not be imported explicilty and is imported automatically when gdrive is imported.
All the commands and the functions that can be readily used are from this module. The following command gives the list of commands callable.
From python console, **gdrive.help()** can be used.
::

   $ gd -h

   usage: gd [-h] func ...

   <func> = function name
   <args> = arguements

   Overview of initializing/listing fucnctions:
  --------------------------------
  'init'   : initialize gdrive, add new parents to initialized dir., add new clients
  'status' : show parents list, show stage list, show users and clients list
  'reset'  : changes default parent, client secrets
             changes parent information like user_names, paths, root folders (Ex: shared drives), clients
             deletes parents, delete authentication data,
  'ls'     : lists all files/folders in parent paths, shows registered usernames and their shared drives, clients
  'find'   : Searches for files and folders based on query
  'cd'     : changes parent_path directly without using 'reset' function
  'mkdir'  : creates new folder in the parent or path provided
  'rm'     : creates existing folder/file in the parent or path provided

   Overview of push/pull functions:
   ---------------------------------
   'add'    : adds paths to the stage, clear stage
   'push'   : uploads files/folders to parent_paths
   'pull'   : downloads files/folders from parent_paths

   Miscelleneous functions:
   ---------------------------------
   'help'   : Shows the list of functions or commands available
   'rmgd'   : Removes the gd file created by importing gdrive
   'default' : Brings the package to its default state (removes all clients, auth. data and the gd commandline functionality)
   'version' : Prints the current version

   positional arguments:
     func
     args

   optional arguments:
  -h, --help  show this help message and exit
  

Initilizing/Listing:
-----------------------
.. currentmodule:: gdrive.gd
.. autofunction:: init

.. currentmodule:: gdrive.gd
.. autofunction:: status

.. currentmodule:: gdrive.gd
.. autofunction:: reset

.. currentmodule:: gdrive.gd
.. autofunction:: ls

.. currentmodule:: gdrive.gd
.. autofunction:: find

Query for gdrive.find:
*************************
A query must be passed as a string enclosed by " ". It can have only the following logical operators - **and**, **or** and **not**. All the contents must be separated by **spaces** as shown in examples below. **not** applies to the immediate next word. Similarly, **and** and **or** considers the immediate string if there is no **not**, otherwise the next two strings including **not**. * is the wildcard character which can be used to fill in unknown strings. To search for only files, append **%f** in the beginning of the query and for only folders, append **%d**. See examples below:

::

  "*.jpg* and *fruit* or *.tif*"     -  Searches files and folders ending with .jpg 
                                        and having 'fruit' in title, or files and 
                                        folders ending with .tif

  "U* and *Y"                        -  Searches files and folders names which start 
                                        with U and end with Y.

  "%f U*Y"                           -  Searches files which 
                                        start with U and end with Y.

  "*.*"                           	 -  Searches files and folders containing '.'

  "%d F*T and not *.* and not FART"  -  Seaches for folders starting with F and 
                                        ending with T, but with no extension and not FART.

.. currentmodule:: gdrive.gd
.. autofunction:: cd

.. currentmodule:: gdrive.gd
.. autofunction:: mkdir

.. currentmodule:: gdrive.gd
.. autofunction:: rm

Upload/Download:
--------------------
.. currentmodule:: gdrive.gd
.. autofunction:: add

.. currentmodule:: gdrive.gd
.. autofunction:: push

.. currentmodule:: gdrive.gd
.. autofunction:: pull

Miscellaneous:
--------------------
.. currentmodule:: gdrive.gd
.. autofunction:: help

.. currentmodule:: gdrive.gd
.. autofunction:: rmgd

.. currentmodule:: gdrive.gd
.. autofunction:: default

.. currentmodule:: gdrive.gd
.. autofunction:: version


gdrive.drive\_util module
####################

These functions are utility functions which are used in gd to control files in gdrive. The functions here take pyDrive.GoogleDrive() object as an arguement to do this.

.. automodule:: gdrive.drive_util
   :members:
   :undoc-members:
   :show-inheritance:

gdrive.auth\_util module
####################

This module contains functions which are responsible for managing the pyDrive.GoogleAuth() object. The functions here are used in gd to authenticate users, check for username cedentials and adding client files on the system.

.. automodule:: gdrive.auth_util
   :members:
   :undoc-members:
   :show-inheritance:
