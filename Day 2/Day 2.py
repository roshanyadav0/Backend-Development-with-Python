# immutables types = means that we cannot change the value of the variable after it has been created

# int, float, bool, str, tuple, frozenset

# mutable types = means that we can change the value of the variable after it has been created

# list, set, dict

# casting 
a = int("322")
print(a)

b = float("3.14")

print(type(a))

# conversion
print(type(float(a)))
a = float(a)
print(type(a))

# isinstance() function is used to check if an object is an instance of a class or a subclass thereof.

print(isinstance(a,int))

# type converter from int to str
hero = 'h'
print(hero)
print(type(hero))
hera = "hero"
print(hera)
character = 'c'
character = str(character)
print(character)
print(type(character))
