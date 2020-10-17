import subprocess
from multiprocessing import Pool
import os

def backup(directory):
    subprocess.call(["rsync", "-arq", src + directory, dest])

if __name__ == "__main__":
    home = os.getcwd()
    src = home + "/data/prod/"
    dest = home + "/data/prod_backup/"
    directories = os.listdir(src)
    p = Pool(len(directories))
    p.map(backup, directories)