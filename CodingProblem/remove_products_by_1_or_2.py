from collections import Counter

locations = [1,8,6,7,7]
location_counter = Counter(locations)
steps = 0
print(f"Step {steps}: {location_counter}")

while location_counter:
    # at least 2 elements
    if len(location_counter) > 1:
        top_two_keys = location_counter.most_common(2)
        for key, _ in top_two_keys:
            location_counter[key] -= 1
            # Remove key if count reaches 0
            if location_counter[key] == 0:
                del location_counter[key]
        steps += 1
    # exactly 1 element
    else:
        location_counter.clear()
        steps += 1
    print(f"Step {steps}: {location_counter}")