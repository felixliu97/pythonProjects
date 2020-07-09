import os

def new_directory(directory, filename):
  # Before creating a new directory, check to see if it already exists
  if os.path.isdir(directory) == False:
    os.mkdir(directory)

  # Create the new file inside of the new directory
  os.chdir(directory)
  with open (filename, "w") as file:
    pass

  # Return the list of files in the new directory
  path = os.getcwd()# This creates a variable path with the current directory path
  path_list = os.listdir(path)# This creates a list with files and sub-directories within my current directory
  return path_list
print(new_directory("PythonPrograms", "script.py"))