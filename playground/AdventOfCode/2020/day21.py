with open('input-day21.txt', 'r') as f:
    food_list = f.read().strip().split('\n')
    lines = [(ingredients.split(' '), allergens.strip(')').split(', ')) for ingredients, allergens in [line.strip().split(' (contains ') for line in food_list]]

    dict = {}
    final = {}
    all_ingredients, remaining_allergens = [], []

    for ingredients, allergens in lines:
        for ingredient in ingredients:
            all_ingredients.append(ingredient)
        for allergen in allergens:
            if allergen not in dict:
                dict[allergen] = ingredients
            else:
                dict[allergen] = list(set(dict[allergen]).intersection(ingredients))

    for allergen, ingredients in dict.items():
        if len(ingredients) == 1:
            remaining_allergens.append(allergen)
            final[allergen] = ingredients[0]

    while remaining_allergens:
        allergen = remaining_allergens.pop(0)
        ingredient = dict[allergen][0]
        for key, value in dict.items():
            if key not in final.keys():
                if ingredient in value:
                    value.remove(ingredient)
                if len(value) == 1:
                    final[key] = value[0]
                    remaining_allergens.append(key)

    print(f'part 1:', len([x for x in all_ingredients if x not in final.values()]))
    print(f"part 2: {','.join([ingredient for _, ingredient in sorted(final.items())])}")