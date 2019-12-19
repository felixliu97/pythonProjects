import os, glob

os.chdir(r"C:\Users\liusu\Desktop\photos\wedding photos")
for file in glob.glob("*.jpg"):
	print(file)
