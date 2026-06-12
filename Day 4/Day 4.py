# Sets - unordered , unique , hashable elements

fruits = {"kela", "seb", "aam", "kela"}
print(fruits)  # Output will be {'kela', 'seb', 'aam'} - duplicates are removed

# CRUD on sets 

fruits.add("angoor")  # Adding an element to the set
print(fruits)  # Output will include 'angoor'

print("angoor" in fruits)   # Output: True - checking for membership

fruits.discard("seb")  # Removing an element from the set without raising an error if it doesn't exist
fruits.remove("aam")  # Removing an element from the set
print(fruits)  # Output will be {'kela', 'angoor'} - 'seb' and 'aam' are removed

fruits = {"kela", "seb", "aam", "kela"}
# print(fruits[0])  # This will raise an error because sets do not support indexing
print(fruits)

#fruits.add(["angoor", "tarbuj"])  # This will raise an error because lists are not hashable and cannot be added to a set

# set operations

a = {1, 2, 3, 4} 
b = {3, 4, 5, 6}
print(a.union(b))  # Output: {1, 2, 3, 4, 5, 6} - elements present in either set
print(a.intersection(b))  # Output: {3, 4} - elements present
print(a.difference(b))  # Output: {1, 2} - elements present in a but not in b
print(a.symmetric_difference(b))  # Output: {1, 2, 5,

# dictonaries - key value pairs

#create

users = {
    "name": "John",
    "age": 30,
    "city": "New York"
}

#read - safe with .get() method

print(users["name"])
print(users.get("name"))  # Output: John
print(users.get("country", "Not Found"))  # Output: Not Found - default value

# update 

users["age"] = 31  # Updating an existing key
users.update({"city": "Los Angeles", "country": "USA"})  # Updating multiple keys
print(users)  # Output will show updated age, city and new country key

# delete

users["age"] = 31  # Updating an existing key
users.pop("age")  # Removing a key-value pair using pop
users.pop("country", None)  # Removing a key-value pair using pop with default value to avoid KeyError
del users["city"]  # Removing a key-value pair using del
print(users)  # Output will show only the 'name' key remaining

# itration 

users.update({"age": 30, "city": "New York"})  # Adding age and city back for iteration
for key,value in users.items():
    print(key, value)  # Output: name John, age 30, city New York - iterating over key-value pairs


# Nested dictonaries
from pprint import pprint
company = {
    "name": "Acme",
    "teams": {
        "engineering": {
            "head": "Priya",
            "members": ["Raj", "Sam", "Liu"],
            "budget": 500_000
        },
        "design": {
            "head": "Aiko",
            "members": ["Ben", "Mia"],
            "budget": 200_000
        }
    }
}
print(company["teams"]["engineering"]["head"])  # Output: Priya - accessing nested dictionary values

# safe access to nested dictonaries
print(company.get("teams", {}).get("engineering", {}).get("head", "Not Found"))  # Output: Priya - safe access to nested dictionary values

# add new team to the company
company["teams"]["marketing"] = {
    "head": "Carlos",
    "members": ["Ana", "Luis"],
    "budget": 150_000
}

pprint(company)  # Output will include the new marketing team in the company dictionary