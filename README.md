# **gdrive**
## File management for Google Drive using python

[![Documentation Status](https://readthedocs.org/projects/gdrive/badge/?version=latest)](https://gdrive.readthedocs.io/en/latest/?badge=latest)

gdrive helps users to easily access files from Google Drive using paths, instead of File ids. Google API requires the users to know the File ID to access it, but this package which is built using the pyDrive package allows users to use a file path to access the file or folder.

In addition to this, the package also provides commands that can be called from a terminal, like cd, ls, pull or push, to quickly view, modify, download or upload files from or to Google drive using a python code or just the command line.

### Documentation:
For more details about setup and commands, check [gdrive.readthedocs.io](https://gdrive.readthedocs.io).

### DEMO

gdrive can be used as a python package right away, but try the following steps to be able to use gdrive's functions directly from command line.
First, import the gdrive in a python console.
<pre><code>$ python
>> import gdrive
>> gdrive.ROOT_PATH</code></pre>
  
**ROOT_PATH** is the local system path to the gdrive package. Add this path to the **PATH** environment variable.
Now, `gd` can be used as a command in command prompt or bash shell.

#### Quickdemo 1 : Basics

Lets see how gdrive can be used from command line.

Open terminal and set some folder where you intend to download or from where you intend to upload files.

<pre><code>$ gd init</code></pre>
  
When asked for a username, this is not same as the google username. More about this explained in the *username* documentation.
Enter some nickname (for example, ***mygdrive***) you would like to give to your google account, so that you can use this for quick authentication into your account in future.
This should take you to a Oauth Consent screen, where you'll be asked to enter your Google username and password. You are good, if you see this a html page showing this.

>  The authentication is successful.

Once authentication is done, from the current working folder, you can try several gdrive commands. Just like `git`, gdrive also creates a hidden folder **.gd** which contains information about the fileIDs, driveIDs etc. More about this explained in the *parents* documentation.

> :warning: After authentication of a new account, the credentials are stored in **ROOT_PATH/api_data** folder. The contents of this folder must be handled with discretion.

After, initialization and authentication, you can use all the gdrive commands from this directory.

<pre><code>$ gd status
---------------
Parent dicts :
---------------
// origin // <DEFAULT>
username : mygdrive
path     : ''
id       : 'root'
drive    : 'My Drive'
driveId  : 'root'
client_sec : 'client_secrets'

No files/folders staged.
</code></pre>

This command shows the contents of **.gd/.gdinfo.json** file created during initialization. The structure of this and the meaning of each term are explained in the *parents* documentation. For example, the folders in my drive are in this hierarchy.

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
</code></pre>

To list my files in the path stored in the **path** variable of the dictionary showed above:

<pre><code>$ gd ls
: D[2351.5kB] 1 : fruits
: D[6571.2kB] 2 : flowers
 </code></pre>

**My Drive** is the name of the google drive's root folder. **''** (empty string) denotes the path to it. This shows that there are two folders in my root folder - fruits and flowers.

<pre><code>$ gd ls fruits/hard
: f[1000.5kB] 1 : apple.jpg
: F[321.0kB] 2 : guava.jpg</code></pre>

This is how the paths can be simply used to get the file contents. Now, I'll change my path from *''* to *'fruits/hard'*:

<pre><code>
$ gd cd fruits/hard
origin cwd changed to 'fruits/hard'

$ gd ls
: f[1000.5kB] 1 : apple.jpg
: F[321.0kB] 2 : guava.jpg

$ gd status
---------------
Parent dicts :
---------------
// origin // <DEFAULT>
username : mygdrive
path     : 'fruits/hard'
id       : '34eWf..iT23'
drive    : 'My Drive'
driveId  : 'root'
client_sec : 'client_secrets'

No files/folders staged.
</code></pre>

If I want to download the folder:

<pre><code>$ gd pull</code></pre>

Or, to just download the *apple.jpg*:

<pre><code>$ gd pull origin apple.jpg</code></pre>

If I want to upload *berry.png* to **fruits/hard**:

<pre><code>$ gd add <local_path_to_'berry.png'>
$ gd cd fruits/hard
$ gd push</code></pre>


#### Quickdemo 2 : Multiple Parent functionality

**.gd/.gdinfo.json** is a dictionary with each key defined as a parent (just like a remote in git). The first key of this dictionary is 'default_parent' whose value is the name of a default parent. Multiple parents can be set with multiple usernames(i.e. google accounts), paths, shared drives or even different client secrets files and one of these can be given the status of 'default_parent'. This makes frequent uploading and downloading as easy as git pull and push functions.

To add a new parent:

<pre><code>$ git init -add</code></pre>

Once a parent is added (say, origin2), we can assign different parameters (like username, path etc.) and push files simultaneously

<pre><code>$ git push origin origin2</code></pre>


#### Quickdemo 3 : Use of these commands in python script:

All these commands can be used in a python script as shown below. The only difference from the terminal commands is that apart from the main function (init, status, etc), the optional arguements must be passed as strings in a list. If there is no arguements, an empty list must be passed in the function.

<pre><code>>> import gdrive as gd
>> 
>> gd.init([])
>> gd.status([])
>> gd.add(['berry.jpg', 'mango.jpg'])</code></pre>

For more details, check [gdrive.readthedocs.io](https://gdrive.readthedocs.io)


#### Please post issues here or email me at preeth@uw.edu
