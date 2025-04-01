def min_hours_to_equalize(servers):
    if len(servers) <= 1:
        return 0
    max_band = max(servers)
    # print(f"max_band:{max_band}")
    total_odd = total_even = 0
    for server in servers:
        diff = max_band - server
        # print(f"diff:{diff}")
        odd_needed = diff % 2
        even_needed = diff // 2
        total_odd += odd_needed
        total_even += even_needed
    while total_even > total_odd * 2:
        total_even -= 1
        total_odd += 2
    print(f"total_odd:{total_odd},total_even:{total_even}")
    latest_odd = total_odd * 2 - 1 if total_odd else 0
    latest_even = total_even * 2
    return max(latest_odd, latest_even)

# Example from the problem statement
servers = [1, 2, 4]
result = min_hours_to_equalize(servers)
print(f"For servers {servers}, minimum hours to equalize: {result}")

# Step by step for the example [1, 2, 4]:
# Target = 4:
#   Server 1 (value 1): deficit = 3, needs 1 odd hour and 1 even hour
#   Server 2 (value 2): deficit = 2, needs 1 even hour
#   Server 3 (value 4): deficit = 0, needs no operations
#   Total: 1 odd hour operation, 2 even hour operations
#   Schedule: Hour 1 (odd): Server 1, Hour 2 (even): Server 1, Hour 4 (even): Server 2
#   Total hours: 4

# Additional test cases
test_cases = [
    [1, 1, 1],       # Already equal
    [3, 1, 5],       # Another test case
    [5, 5, 9],       # Larger difference
    [10, 10, 10, 11] # One outlier
]

for servers in test_cases:
    hours = min_hours_to_equalize(servers)
    print(f"For servers {servers}, minimum hours to equalize: {hours}")