#! /usr/bin/env python3
import os
import requests

ip = "http://35.238.113.144/"

list_of_files = os.listdir('/data/feedback')
for file in list_of_files:
    fp = open('/data/feedback/'+file)
    data = fp.read().split('\n')
    dic = {"title": data[0], "name": data[1], "date": data[2], "feedback": data[3]}
    response = requests.post(ip + 'feedback/', json=dic)
    print(response.status_code)
