import re

def str_has_number(str):
    return bool(re.search(r'\d', str))

def list_has_number(list):
    for str in list:
        if str_has_number(str):
            return True
    return False

def count_match(regex, messages):
    match = 0
    for message in messages:
        if re.match(r'^' + regex + r'$', message):
            match += 1
    return match

# with open('input-test.txt', 'r') as f:
with open('input-day19.txt', 'r') as f:
    text = f.read().strip().split('\n\n')
    rules = text[0].split('\n')
    messages = text[1].split('\n')

    dict = {}
    dict2 = {}
    converted, converted2, visited, visited2 = [], [], [], []

    for rule in rules:
        rule_num = rule.split(':')[0]
        values = rule.split(':')[1].strip()
        if 'a' in values or 'b' in values:
            char = values[1].strip('"')
            converted.append((rule_num, char))
            visited.append(rule_num)
            dict[rule_num] = char
            converted2.append((rule_num, char))
            visited2.append(rule_num)
            dict2[rule_num] = char
        else:
            dict[rule_num] = values.split()
            dict2[rule_num] = values.split()

    while converted:
        s = converted.pop(0)
        num = s[0]
        chars = s[1]
        for key, value in dict.items():
            if key not in visited:
                if num in value:
                    if len(chars) > 1:
                        chars = '(' + chars + ')'
                    dict[key] = [re.sub(r'\b'+ num + r'\b', chars, w) for w in value]
                if not list_has_number(dict[key]):
                    new_val = ''.join(dict[key])
                    converted.append((key, new_val))
                    visited.append(key)

    reg1 = r'^' + ''.join(dict['0']) + r'$'
    print(f'part 1 matches:', count_match(reg1, messages))

    # hack of rule
    dict2['8'] = '42 | 42 +'.split()
    dict2['11'] = '42 31 | 42 42 31 31 | 42 42 42 31 31 31 | 42 42 42 42 31 31 31 31'.split()

    while converted2:
        s = converted2.pop(0)
        num = s[0]
        chars = s[1]
        for key, value in dict2.items():
            if key not in visited2:
                if num in value:
                    if len(chars) > 1:
                        chars = '(' + chars + ')'
                    dict2[key] = [re.sub(r'\b'+ num + r'\b', chars, w) for w in value]
                if not list_has_number(dict2[key]):
                    new_val = ''.join(dict2[key])
                    converted2.append((key, new_val))
                    visited2.append(key)
    
    reg2 = r'^' + ''.join(dict2['0']) + r'$'
    print(f'part 2 matches:', count_match(reg2, messages))