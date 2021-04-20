gdrive2 Functions and Commands
==============

The following submodules are present in the package:
::

   gdrive2
   |_______gd
   |_______drive_util
   |_______auth_util
   |_______paths

The main module that is automatically imported when gdrive2 is imported is **gdrive2.gd**.Other modules are utility modules, whose functions are used in **gd**. **paths** module only contains file paths which are imported as constants in other modules.

gdrive2.gd module
####################

This module need not be imported explicilty and is imported automatically when gdrive2 is imported.
All the commands and the functions that can be readily used are from this module. The following command gives the list of commands callable.
From python console, **gdrive2.help()** can be used.
::

   $ gd -h

   usage: gd [-h] func ...

   <func> = function name
   <args> = arguements

   Overview of initializing/listing fucnctions:
  --------------------------------
  'init'   : initialize gdrive2, add new parents to initialized dir., add new clients
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
   'rmgd'   : Removes the gd file created by importing gdrive2
   'default' : Brings the package to its default state (removes all clients, auth. data and the gd commandline functionality)
   'version' : Prints the current version

   positional arguments:
     func
     args

   optional arguments:
  -h, --help  show this help message and exit
  

Initilizing/Listing:
-----------------------
.. currentmodule:: gdrive2.gd
.. autofunction:: init

.. currentmodule:: gdrive2.gd
.. autofunction:: status

.. currentmodule:: gdrive2.gd
.. autofunction:: reset

.. currentmodule:: gdrive2.gd
.. autofunction:: ls

.. currentmodule:: gdrive2.gd
.. autofunction:: find

Query for gdrive2.find:
*************************
A query made with `fnmatch <https://docs.python.org/3/library/fnmatch.html>`_ (slighlty different from glob) patterns must be passed as a string enclosed by " ". It can have only the following logical operators - **and**, **or** and **not**. All the fnmatch patterns and the operators must be separated by **spaces** as shown in examples below. **not** operates on the immediately following pattern. Similarly, **and** and **or** operates on the following pattern or on the result of a **not** operation. To search for only files, append **%f** in the beginning of the query and for only folders, append **%d**. In the and-separated query, the first string (after %f, %d or not, if present) sets the initial list of paths. The latter strings or conditions connected by 'and' to the previous one must lead to a subset of paths of the previous list. For the conditions connected by 'or', they are evaluated separately and the final list is the union of the sets obtained from individual condition evaluations. See examples below:

Consider a file hierarchy as shown below for example:

::

	My Drive                                  - - - - - - - tier 1
	|
	|___fruits                                - - - - - - - tier 2
	|      |___hard                           - - - - - - - tier 3
	|      |     |__apple.jpg                 - - - - - - - tier 4
	|      |     |__guava.png                 - - - - - - - tier 4
	|      |
	|      |___soft                           - - - - - - - tier 3
	|            |__grapes.jpg                - - - - - - - tier 4
	|
	|___flowers                               - - - - - - - tier 2
	      |___yellow                          - - - - - - - tier 3
	      |      |__sunflower.tiff            - - - - - - - tier 4
	      |
	      |___red                             - - - - - - - tier 3
	           |__roses.jpg                   - - - - - - - tier 4
	           |__poppy.png                   - - - - - - - tier 4

For the above drive, following are some examples for the query use for tier = 4 files,
with *--path-search* option (searches entire paths to the files in the specified tier 
instead of just filenames at in the tier) enabled:

::

  "*.jpg* and *soft* or *.png*"     -  Searches files and folders ending with .jpg 
                                        and having 'soft' in pathname, or files and 
                                        folders ending with .png
  
                                        1. fruits/soft/grapes.jpg
                                        2. fruits/hard/guava.png
                                        3. flowers/red/poppy.png

  "f* and *f"                       -  Searches files and folders names which start 
                                        with f and end with f.

                                        1. flowers/yellow/sunflower.tiff

  "%f f*ng"                         -  Searches files which 
                                        start with f and end with ng.

                                        1. fruits/hard/guava.png
                                        2. flowers/red/poppy.png

  "*.*"								-  Searches files and folders containing '.'

										1. fruits/hard/apple.jpg
										2. fruits/hard/guava.png
										3. fruits/soft/grapes.jpg
										4. flowers/yellow/sunflower.tiff
										5. flowers/red/roses.jpg
										6. flowers/red/poppy.png


  "%d f*g and not png"  			-  Seaches for folders starting with f and 
                                        ending with g, but not png files.

                                        1. fruits/hard/apple.jpg
  										2. fruits/soft/grapes.jpg
  										3. flowers/red/roses.jpg

Fnmatch Wilcard characters:
*****************************
+--------------+----------------------+
|   Wildcard   |       Meaning        |
+==============+======================+
|      *       | matches everything   |
+--------------+----------------------+
|      ?       | matches any single   |
|              | character            |
+--------------+----------------------+
|    [*seq*]   | matches any character|
|              | in *seq*.            |
+--------------+----------------------+
|   [!*seq*]   | matches any character|
|              | not in *seq*.        |
+--------------+----------------------+
Note that these do not have ** character as in glob patterns. To get the functionality of path search, use *--path-search* arguement
in **gdrive2.find** or **path_search = True** in **gdrive2.drive_util.query_to_paths()**.


.. currentmodule:: gdrive2.gd
.. autofunction:: cd

.. currentmodule:: gdrive2.gd
.. autofunction:: mkdir

.. currentmodule:: gdrive2.gd
.. autofunction:: rm

Upload/Download:
--------------------
.. currentmodule:: gdrive2.gd
.. autofunction:: add

.. currentmodule:: gdrive2.gd
.. autofunction:: push

.. currentmodule:: gdrive2.gd
.. autofunction:: pull

Miscellaneous:
--------------------
.. currentmodule:: gdrive2.gd
.. autofunction:: help

.. currentmodule:: gdrive2.gd
.. autofunction:: rmgd

.. currentmodule:: gdrive2.gd
.. autofunction:: default

.. currentmodule:: gdrive2.gd
.. autofunction:: version


gdrive2.drive\_util module
####################

These functions are utility functions which are used in gd to control files in gdrive2. The functions here take pyDrive.GoogleDrive() object as an arguement to do this.

.. automodule:: gdrive2.drive_util
   :members:
   :undoc-members:
   :show-inheritance:

gdrive2.auth\_util module
####################

This module contains functions which are responsible for managing the pyDrive.GoogleAuth() object. The functions here are used in gd to authenticate users, check for username cedentials and adding client files on the system.

.. automodule:: gdrive2.auth_util
   :members:
   :undoc-members:
   :show-inheritance:
