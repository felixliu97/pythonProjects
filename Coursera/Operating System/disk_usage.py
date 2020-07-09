import shutil
import psutil
import requests
import socket

def check_disk_usage(disk):
    du = shutil.disk_usage(disk)
    free = du.free / du.total * 100
    return free

def check_cpu_usage():
    usage = psutil.cpu_percent(1)
    return usage

du = check_disk_usage("/")
usage = check_cpu_usage()

print("Disk usage is {}%, CPU usage is {}%".format(du, usage))

if (du <= 20 or usage >= 75):
    print("ERROR!")
else:
    print("Everything is OK!")

request = requests.get("http://www.google.com")
print(request.status_code)