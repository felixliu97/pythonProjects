with open('input-day6.txt', 'r') as f:
    text = [group.replace('\n', ' ').strip(' ') for group in f.read().split('\n\n')]
    text2 = [x.replace(' ', '') for x in text]
    all_answers = [len(set(x)) for x in text2]
    distinct_answers = 0
    # print(text)
    for group in text:
        answers = group.split(' ')
        common = answers[0]
        for answer in answers[1:]:
            common = set.intersection(set(common), set(answer))
        distinct_answers += len(common)
    print(sum(all_answers), distinct_answers)