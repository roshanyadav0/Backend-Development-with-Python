# Core concept of Serialization and Deserialization

# SerializationPython object → JSON (saving/sending)
# DeserializationJSON → Python object (loading/reading)


import json

# json.load() Read from a file 
with open("data.json","r") as f:
    data = json.load(f)  # file object -> python dictonary


# json.loads() → reads from a STRING
json_string = '{"name": "Alice", "age": 25}'
data = json.loads(json_string)   # string → Python dict
print(data["name"])              # Alice

# 3. json.dump() vs json.dumps()

person = {"name": "Alice", "age": 25, "hobbies": ["reading", "coding"]}

# json.dump()  → writes to a FILE
with open("data.json", "w") as f:
    json.dump(person, f, indent=4)   # Python dict → file

# json.dumps() → writes to a STRING
json_string = json.dumps(person, indent=4)
print(json_string)
# {
#     "name": "Alice",
#     "age": 25,
#     "hobbies": ["reading", "coding"]
# }


# 5. Handle Missing / Corrupt JSON Files

def load_files(filepath):
    try : 
        with open(filepath , "r") as f:
            return json.load(f)
    except FileExistsError :
        print("File not found. Starting fresh")
        return [] # safe default 
    except json.JSONDecodeError :
        print("File is corrupt or invalid JSON. Starting fresh.")
        return [] # safe default 
    