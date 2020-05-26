# **gdrive**
## File management for Google Drive using python (Readme under construction)

**gdrive** is inspired from git's push-pull functionalities from command line. This is built using [pyDrive](https://github.com/gsuitedevs/PyDrive). **gdrive** allows easy access to google drive files without IDs, but with just file paths. With gdrive, some command line functions like `cd` and `ls` can be used to view files in drive folders directly from command line.

## Setup 
Use the following command to install the package.
(The package is still under testing)

```pip install -i https://test.pypi.org/simple/ gdrive```

## Requirements

1. PyDrive library is required for this. To install Pydrive :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; for PIP : use command

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;```pip install PyDrive```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; for ANACONDA : use command

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;```conda install -c conda-forge pydrive```

2. A client secrets file is required. Read [client_name](#client_name) below.

3. After installing `gdrive`, try the following steps to be able to use gd from command line.

&nbsp;&nbsp;&nbsp;First, import the gdrive in a python console.

<pre><code>$ python
>> import gdrive
>> gdrive.ROOT_PATH
</code></pre>

This will show path to the gdrive package. Add this path to the `PATH` environment variable.
Now, `gd` can be used as a command in command prompt or bash shell.

## Data structuring

### Parents

For convenient pushing and pulling files from various folders and google drive accounts with multiple api clients, a ***parent*** structure is used. When a working directory is ***initialized***, multiple ***parents*** can be used to store paths and ids for multiple google drives. Each ***parent*** is a list of other data like username, parent_path, parent_id, drive_name, drive_id and client_name stored as strings. All the parents are stored as dictionary items as shown below with the `parent_name` being the name or key of the parent.

<pre><code>parent_name : [
      username,
      parent_path,
      parent_id,
      drive_name,
      drive_id,
      client_name
]
</pre></code>


`init` function is used to initialize a directory which creates a **.gd** folder in it with the following contents.
<pre><code>cwd
|__.gd
    |__.gdinfo.json
    |__.gdstage
</pre></code>

Each `.gdinfo.json` is a dictionary of ***parents***, defined by user for that directory.

For example, the user can initialize a directory and define ***parents*** as shown below, which are saved in the .gd/.gdinfo.json.

<pre><code>>> cat .gdinfo.json
{default_parent : 'origin',
'origin' : [
      'preetham_acc',
      'fruits',
      '1bW2H.....uY4on',
      'Shared drive 1',
      'nZTvt.....4kt9',
      'client_secrets'
],
'test' : [
      'paul_acc',
      'flowers/yellow',
      'WEpIZu.....HE3L7B',
      'My Drive',
      'root',
      'client_secrets'
]}
</pre></code>

The **default_parent** has a string as its value, which is one of the parent_names.

### username

The ***usernames*** used in parents are different from the google usernames (like in <google_username>@gmail.com). Each ***username*** corresponds to a single <google_username>, but each <google_username> can have multiple ***usernames***. A ***username*** is basically a nickname the user gives to their google account for easy pushing and pulling files. Once, a ***username*** is defined, the ***username*** can be used for other parents in different directories to use the same google account.

### parent_path and parent_id

The ***parent_path*** is the path to a folder in drive in the google account registered with the nickname ***username***. For example, assume a drive like this:

<pre><code>My Drive
|
|___fruits
|      |___hard
|      |     |__apple.jpg
|      |     |__guava.png
|      |
|      |___soft
|            |__grapes.jpg
|
|___flowers
      |___yellow
      |      |__sunflower.tiff
      |
      |___red
           |__roses.jpg
           |__poppy.png
</pre></code>

The path to the ***sunflower.tiff*** folder would be:

<pre><code>flowers/yellow/sunflower.tiff</pre></code>

Note that the root folder here is ***My Drive***, which will not be included in the path. The same path representation is followed for the folders in shared drives. 

Each file or folder in google drive has an ***ID***. See [this](https://developers.google.com/drive/api/v3/reference/files) to know more about file metadata in google drive. A ***parent_id*** is the ID of the folder at the ***parent_path***.

### drive_name and drive_id

This is the name of the drive in which the ***parent_path*** is located. Each google account can have multiple shared drives along with the main ***"My Drive"***. ***drive_id*** is the ID of this drive.

### client_name

To use Google Drive API, an application has to be created using the [Google Cloud Console](console.cloud.google.com). To obtain a client secrets file, create an application as shown below.

1. Open the console and create a new project.
2. After assigning name and organisation to the project, go to **APIs & Services --> Dashboard**
3. Go to **OAuth consent screen** and configure a consent screen. Assign an application name and other details.
4. Go to **Credentials --> Create Credentials --> OAuth client ID**
5. For Application type, use **Web Application** and assign a name to it.
6. For Authorized java script origins, use:
<pre><code>http://localhost:8080</pre></code>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; For Authorized redirect URIs, use:
<pre><code>http://localhost:8080/</pre></code>
7. Click "Create"

Once credentials are created, they can be downloaded as a ***.json*** file with the name ***client_secrets<some_long_id>.json***.
This file can be renamed as <***client_name***>.json and can be used to access parent_path. If gdrive is being used for the time, it asks the user to show the file location of a client secrets file and creates a default file - ***client_secrets.json***. Later, more such files can be added with different ***client_names*** as <client_name1>.json, <someother_user_specified_name>.json etc. Each parent can be assigned a ***client_name*** different from the default name - ***client_secrets***.
