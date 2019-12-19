import random

exclude = random.sample(range(1, 35), 7)
exclude.sort()
#exclude = [12, 13, 16, 18, 24, 28, 33, 36, 40, 43] #randomly generated at 15:05:00 PM, 11 July 2019
print(exclude)
bucket1 = list(range(1, 12))
bucket2 = list(range(13, 24))
bucket3 = list(range(25, 35))

for i in range(36):
  low_numbers = [x for x in bucket1 if x not in exclude]
  random.shuffle(low_numbers)
  mid_numbers = [y for y in bucket2 if y not in exclude]
  random.shuffle(mid_numbers)
  high_numbers = [z for z in bucket3 if z not in exclude]
  random.shuffle(high_numbers)
  result = low_numbers[:2] + mid_numbers[:3] + high_numbers[:2] # guess 2 3 2 distribution in 3 buckets 
  result.sort()
  print(result, "P:", random.randint(11, 20)) #guess powerball in this range