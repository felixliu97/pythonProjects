import re

con = "''"
con2 = "1"

m = re.match(r"'\d+'", con)
if m:
    print("match m")

m2 = re.match(r"'\d+'", con2)
if m2:
    print("match m2")