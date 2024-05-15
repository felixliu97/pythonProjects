import os

with open(os.path.join(os.getcwd(), "input.txt"), "r") as input_file:
    deduplicated_ids = sorted(set(input_file.read().splitlines()))

with open(os.path.join(os.getcwd(), "output.txt"), "w") as output_file:
    output_file.write("\n".join(deduplicated_ids))
