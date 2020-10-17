#!/usr/bin/env python3
import subprocess
from multiprocessing import Pool
import os

src = '/data/prod/'
dest = '/data/prod_backup/'

def run(dirname):
    subprocess.call(["rsync", "-arq", src + dirname, dest + dirname])

if __name__ == "__main__":
    for root, dirs, files in os.walk(src):
        if len(dirs) > 0:
            break
    p = Pool(len(dirs))
    p.map(run, dirs)