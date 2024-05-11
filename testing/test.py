import os

in_path = os.path.join(os.getcwd(), "input.txt")
output_path = os.path.join(os.getcwd(), "output.txt")

with open(in_path, "r") as file:
    ids = file.read().splitlines()

sorted_ids = sorted(ids)
deduplicated_ids = list(dict.fromkeys(sorted_ids))

with open(output_path, "w") as file:
    file.write("\n".join(deduplicated_ids))