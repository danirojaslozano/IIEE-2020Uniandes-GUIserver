# ServerGUI

## How to run the server GUI?
1. Clone the git: <br>
-On Mac: Open the terminal and go to the folder where will save the repository
```ruby
cd /FolderNameWhereTheRepositoryWillSave
clone git https://github.com/danirojaslozano/IIEE-2020-Uniandes.git
```
2. Open the serverGUI folder
```ruby
cd serverGUI
```
3. Activate virtual enviorement:<br>
-On Mac:
```ruby
source envirtual-py 
```
4. Run server:
```ruby
python3 run.py:
```

## Extra info
### Requirements:
If you don't want to use the virtual environment, it's necessary install all the libraries in requirements list.
```ruby
pip3 install -r requirements.txt
```
### Folders:
- *Static Folder*: Has all the images about the app.
- *Templates Folder*: Has the HTML code about the web app.
- *Results Folder*: where is the Data Folder.
- *Data Folder*: Has all the files with acquired data using MPU5060 
- *envirtual-py Folder*: Libraries and files for the virtual environment.
