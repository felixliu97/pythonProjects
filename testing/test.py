import json

def process_data(data):
    # Check if it's a JSON object or a JSON array
    if isinstance(data, dict):
        print("It's a JSON object")
        # Process as a JSON object
        print(f"Name: {data['name']}, Age: {data['age']}")
    elif isinstance(data, list):
        print("It's a JSON array")
        # Process as a JSON array
        for item in data:
            print(f"Name: {item['name']}, Age: {item['age']}")
    else:
        print("Unknown JSON structure")

# Sample JSON strings (could be an object or an array)
json_string_object = '{"name": "John", "age": 30}'
json_string_array = '[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]'

data = json.loads(json_string_object)  # Replace with json_string_array to test the array case
process_data(data)

data = json.loads(json_string_array)  # Replace with json_string_array to test the array case
process_data(data)