import time

def scheduler(func, sec):
    while True:
        time.sleep(sec)
        func()

def func1():
    print("Function 1")

def func2():
    print("Function 2")

# scheduler(func1, 2)
scheduler(func2, 3)