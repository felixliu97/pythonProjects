import re

passports = {}
count, match1, match2 = 1, 0, 0

with open('input-day4.txt', 'r') as f:
    for line in f.readlines():
        line = line.strip()
        if line:
            if count not in passports:
                passports[count] = line
            else:
                passports[count] += ' ' + line
        else:
            count += 1

for id, passport in passports.items():
    attr = passport.split(' ')
    attr.sort()
    str = ' '.join(attr)
    str = ' ' + str
    # print(str)
    if re.match(r'.*byr:.*ecl:.*eyr:.*hcl:.*hgt:.*iyr:.*pid:.*', str):
        # print("match1")
        match1 += 1
    if re.match(r' byr:(19[2-9][0-9]|200[0-2])( cid:.*)? ecl:(amb|blu|brn|gry|grn|hzl|oth) eyr:(202[0-9]|2030) hcl:#[a-f0-9]{6} hgt:(1([5-8][0-9]|9[0-3])cm|(59|6[0-9]|7[0-6])in) iyr:(201[0-9]|2020) pid:[0-9]{9}$', str):
        # print("match2")
        match2 += 1

print(match1, match2)