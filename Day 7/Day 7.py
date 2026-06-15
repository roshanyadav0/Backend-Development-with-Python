# positional and keyword arguments

def greet(name,greeting = "Hello") :
    return f"{greeting},{name}"

# positional - order matters 
print(greet("Alice", "Hi"))

# keyword - order dosen't matter
print(greet(greeting = "Adios",name = "John"))

# mixed : positional first , keyword after
print(greet("Hira",greeting = "Previet"))

# print(greet(greeting="Hola","Daryl"))  worng

# *args  (Tuples)

def add(*numbers) :
    print(sum(numbers))

add(1,2,3,4,5)
add(3,4,5)

# unpacking a list into positional args

list = [2,4,34,56,2,754,48]
add(*list)  # * is used for unpacking list to tuples and * is not casting

# **kwargs (Dictonary)

def describe(**attrs):
    for key, val in attrs.items():
        print(f"{key}: {val}")

describe(name="Eve", age=30, city="Delhi")
# attrs = {'name': 'Eve', 'age': 30, 'city': 'Delhi'}
# name: Eve
# age: 30
# city: Delhi

# unpacking a dict into keyword args
info = {"name": "Sam", "age": 25}
describe(**info)   # same as describe(name="Sam", age=25)


# Defaults and aPitfall 
# ✅ safe — immutable default
def greet(name="World"):
    return f"Hello, {name}!"

# ❌ PITFALL — mutable default is created once
def append_to(item, lst=[]):
    lst.append(item)
    return lst

append_to(1)   # → [1]   (looks fine)
append_to(2)   # → [1, 2]  ← shared state! bug!

# ✅ fix — use None as sentinel
def append_to(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst