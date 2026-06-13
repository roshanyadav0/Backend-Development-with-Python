# Day 1
a = 13
print(f"Hello,world {314} {3.14} {True} {None}  ")
print(f"hello {a}")

# Day 2

# isinstance() function is used to check if an object is an instance of a class or a subclass thereof.

num = int(input("enter a number: "))
print(isinstance(num,int))

# Day 3

# slicing

fruits = ['seb','kela','aam','santra']
print(fruits[1:4])

print(fruits[::2]) # everty 2nd 

print(fruits[::-1]) # reverse

# fruits[Starting point : Ending Point : Skipping point]

# Unpacking Tuples 

tup = {3,4,5,6,7}
a,b,*c = tup
print(a)

# Flattening the matrix

m = [
    [1,2,3],
    [4,5,6],
    [7,8,9]
]

flat = [num for row in m for num in row]
print(flat)

# Day 4
# Safe acess in dictionary

dict = {"name": "John", "age": 30, "city": "New York"}
print(dict.get("name", "Not found")) # safe acess if not found than return " Not found"  # Output: John


