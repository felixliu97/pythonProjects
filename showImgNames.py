import os, glob

os.chdir(r"C:\Users\felix.liu\Desktop\music")
for file in glob.glob("*.mp3"):
    print(file)