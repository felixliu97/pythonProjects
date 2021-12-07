import re
import numpy as np

with open('input-day16.txt', 'r') as f:
    tickets = [line.strip() for line in f.readlines()]
    ranges = []
    valid_tickets = []
    nearby_tickets, my_ticket = False, False
    errors = 0
    for ticket in tickets:
        if ticket == 'nearby tickets:':
            nearby_tickets = True
            continue
        if ticket == 'your ticket:':
            my_ticket = True
            continue
        if my_ticket:
            own_ticket = [int(x) for x in ticket.split(',')]
            my_ticket = False
        elif not nearby_tickets:
            res = re.match(r'^(.*): (.*)-(.*) or (.*)-(.*)$', ticket)
            if res:
                field = res.group(1)
                a = int(res.group(2))
                b = int(res.group(3))
                c = int(res.group(4))
                d = int(res.group(5))
                ranges.append((field, a, b, c, d))
        else:
            numbers = [int(x) for x in ticket.split(',')]
            rowError = False
            for num in numbers:
                error = True
                for range in ranges:
                    if range[1] <= num <= range[2] or range[3] <= num <= range[4]:
                        error = False
                        break
                if error:
                    errors += num
                    rowError = True
            if not rowError:
                valid_tickets.append(numbers)

    print(f'Part 1 errors sum:', errors)

    valid_tickets.append(own_ticket)
    #convert cols to rows
    valid_tickets_col = np.array(valid_tickets).T.tolist()
    column_mapping = {}
    final_mapping = {}

    for i, col in enumerate(valid_tickets_col):
        for range in ranges:
            valid = True
            for num in col:
                if num < range[1] or num > range[4] or (range[2] < num < range[3]):
                    valid = False
                    break
            if valid:
                if i not in column_mapping:
                    column_mapping[i] = [range[0]]
                else:
                    column_mapping[i].append(range[0])
    
    columns = list(column_mapping.keys())
    #while not all columns are mapped
    while columns:
        for key, value in column_mapping.items():
            if len(value) == 1:
                field = value.pop(0)
                final_mapping[key] = field
                columns.remove(key)
                for inner_value in column_mapping.values():
                    if field in inner_value:
                        inner_value.remove(field)

    final = [key for key, value in final_mapping.items() if 'departure' in value]
    product = 1
    for index in final:
        product *= own_ticket[index]
    print(f'part 2 product:', product)