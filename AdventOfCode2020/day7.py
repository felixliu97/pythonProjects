import re

def part1(search_color):
    r = re.compile(r'.*contain.*{}.*'.format(search_color))
    search_list = set(rules) - set(match)
    results = list(filter(r.match, search_list))
    if len(results) != 0:
        match.extend(results)
        for color in results:
            res = re.match(r'^(.+) bags contain.*$', color)
            part1(res.group(1))

def part2(search_color, quantity):
    global total_bags
    r = re.compile(r'^{} bags contain'.format(search_color))
    line = list(filter(r.match, rules))
    bags = re.match(r'.*contain(.*)\.$', line[0])
    other_bags = bags.group(1).split(',')
    for other_bag in other_bags:
        if other_bag != ' no other bags':
            res = re.match(r'^ ([0-9]+) (.+) bag(s)?$', other_bag)
            new_quantity = int(res.group(1))
            new_color = res.group(2)
            total_bags += new_quantity * quantity
            # print(new_quantity, new_color)
            part2(new_color, new_quantity * quantity)

with open('input-day7.txt', 'r') as f:
    rules = [line.replace('\n','') for line in f.readlines()]
    match = []
    search_color = "shiny gold"
    search_quantity, total_bags = 1, 0
    part1(search_color)
    part2(search_color, search_quantity)

    print('{} is contained in {} bags'.format(search_color, len(match)))
    print('{} {} bag(s) need {} bag(s)'.format(search_quantity, search_color, total_bags))