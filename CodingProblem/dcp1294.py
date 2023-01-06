def encode(input: str) -> str:
    output = ""
    count = 1
    current_char = input[0]

    for i in range(1, len(input)):
        c = input[i]
        if c == current_char:
            count += 1
        else:
            output += str(count) + current_char
            current_char = c
            count = 1

    output += str(count) + current_char
    return output

input = "AAAABBBCCDAA"
encoded = encode(input)
print(encoded) # prints "4A3B2C1D2A"
