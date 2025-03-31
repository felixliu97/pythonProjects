def count_unique_viral_substrings_optimized(video, k, is_viral):
    """
    Counts the number of unique non-empty substrings of the video that qualify as viral content
    using a more efficient sliding window approach.
    
    Args:
        video (str): A string representing segments of a video
        k (int): Maximum allowed number of non-viral segments
        is_viral (list): List indicating if each character is viral (1) or non-viral (0)
    
    Returns:
        int: The number of unique substrings that qualify as viral content
    """
    if not video or k < 0:
        return 0
    
    n = len(video)
    viral_letters = [chr(i + ord('a')) for i, val in enumerate(is_viral) if val == 1]
    unique_viral_substrings = set()
    
    for left in range(n):
        non_viral_count = 0
        right = left
        
        while right < n and non_viral_count <= k:
            if video[right] not in viral_letters:
                non_viral_count += 1
            if non_viral_count <= k:
                unique_viral_substrings.add(video[left:right+1])
            right += 1
    
    print(unique_viral_substrings)
    return len(unique_viral_substrings)

# Example usage
video = "abcdef"
k = 2
# Example is_viral array: 'a' and 'c' are viral (1), 'b' is non-viral (0)
is_viral = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Test the optimized solution with the same example
result = count_unique_viral_substrings_optimized(video, k, is_viral)
print(f"Number of unique viral substrings for video '{video}' with k={k}: {result}")