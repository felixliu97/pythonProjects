from collections import Counter

def solve():
    left_list = []
    right_list = []
    
    try:
        with open('input-day1.txt', 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    left_list.append(int(parts[0]))
                    right_list.append(int(parts[1]))
                    
        # Part 1
        left_list.sort()
        right_list.sort()
        
        total_distance = sum(abs(l - r) for l, r in zip(left_list, right_list))
        
        print(f"Total distance: {total_distance}")

        # Part 2
        right_counts = Counter(right_list)
        similarity_score = sum(num * right_counts[num] for num in left_list)

        print(f"Similarity score: {similarity_score}")
        
    except FileNotFoundError:
        print("Error: input-day1.txt not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    solve()
