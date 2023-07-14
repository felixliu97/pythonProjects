import re
import os

file = "/output/folder/file.txt"
tag, filename = os.path.split(file)
print(f"tag:{tag}")
print(f"filename:{filename}")