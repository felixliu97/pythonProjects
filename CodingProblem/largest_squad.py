engagement_scores = [12,14,15,11,16,17,18,18,22,23,24,25,26,27]

engagement_scores.sort()
print(engagement_scores)
max_squad_size = 1
current_squad_size = 1

for i in range(1, len(engagement_scores)):
    print(f"Current:{engagement_scores[i]}")
    if engagement_scores[i] <= engagement_scores[i-1] + 1:
        current_squad_size += 1
        max_squad_size = max(max_squad_size, current_squad_size)
        print(f"current_squad_size:{current_squad_size}, max_squad_size:{max_squad_size}")
    else:
        print("Skip")
        current_squad_size = 1
        remaining = len(engagement_scores) - i
        if remaining <= max_squad_size:
            print(f"Early exit, {i}/{len(engagement_scores)} checked, {remaining} remaining but max_squad_size {max_squad_size}")
            break