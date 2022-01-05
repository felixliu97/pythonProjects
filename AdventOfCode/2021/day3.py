most_common = {}

with open('input-day3.txt', 'r') as f:
    binaries = [line.replace('\n','') for line in f.readlines()]
    for binary in binaries:
        for i in range(len(binary)):
            if binary[i] == '1':
                if i not in most_common:
                    most_common[i] = 1
                else:
                    most_common[i] += 1
            elif binary[i] == '0':
                if i not in most_common:
                    most_common[i] = -1
                else:
                    most_common[i] -= 1

gamma_rate_t = ''.join(['1' if most_common[x] >= 0 else '0' for x in range(len(most_common))])
epsilon_rate_t = ''.join(['0' if most_common[x] > 0 else '1' for x in range(len(most_common))])
print(f"gamma_rate_t: {gamma_rate_t}, epsilon_rate_t: {epsilon_rate_t}")

gamma_rate = int(gamma_rate_t, 2)
epsilon_rate = int(epsilon_rate_t, 2)
print(f"gamma_rate: {gamma_rate}, epsilon_rate: {epsilon_rate}, gamma_rate*epsilon_rate: {gamma_rate*epsilon_rate}")
