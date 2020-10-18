#!/usr/bin/env python3
from PIL import Image
import os, sys

user = os.getenv('USER')
images_dir = '/home/{}/supplier-data/images/'.format(user)

for image_name in os.listdir(images_dir):
    if 'tiff' in image_name:
        image_path = images_dir + image_name
        im = Image.open(image_path)
        new_path = images_dir + image_name.split('.')[0] + '.jpeg'
        im.convert('RGB').resize((600, 400)).save(new_path, 'jpeg')
        im.close()
