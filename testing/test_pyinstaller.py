import time

name = input("Name: ")
age = input("Age: ")
print(f"{name} is {age} years old.")

seconds = 5
for i in range(seconds):
    print(f"Turning off in {seconds - i} second(s)")
    time.sleep(1)