def find_2_nums(target, list):
    for num in list:
        counterpart = target - num
        if counterpart in list and counterpart != num:
            return True
    return False

def find_window(target, list):
    for i in range(0, len(list)):
        sum = list[i]
        for j in range(i+1, len(list)):
            sum += list[j]
            if sum > target:
                break
            if sum == target:
                return(list[i:j])
        

with open('input-day9.txt', 'r') as f:
    nums = [int(line.replace('\n','')) for line in f.readlines()]
    window = nums[:25]
    remaining = nums[25:]
    for n in remaining:
        if not find_2_nums(n, window):
            print('{} is not sum of 2 numbers from previous 25 numbers'.format(n))
            break
        window.pop(0)
        window.append(n)
    new_window = find_window(n, nums)
    print('sum of smallest and largest is {}'.format(min(new_window) + max(new_window)))