# def function and return

def greet(name , age = 32 , greeting = "Hello"):
    print(f"{greeting} {name} , you are {age} years old")

greet("John")


# Return vs None

def add(a,b) : 
    return a+b

def say_hi (a) :
    print(f"Hello ! {a}")

x = add(34,42)

y = say_hi("John")

print(y)

# Multiple return values

def thing_ret (a,b,c) :
    return a-445,b*2,c+1

a,b,c = thing_ret(3,4,5)

print(a,b,c)

# Global and non local keywords

count = 0

def increment() :
    global count
    count += 1

def outer() :
    total = 0
    def add(n) :
        nonlocal total
        total+=n
    add(5)
    add(3)
    return total

increment()
print(outer())

# Dockstring

def celcious_to_fehrenheit (celcius) :
    """ Convert temprature to fehrenheit
    args : 
        celcious float : Temprature in degree celcious
    
    return :
        float : Equivalant temprature in degree fehrenheit
    
    Example : 
        >>> celciout_to_fehrenheit(100)
        212.0
    """
    return celcious* 9/5 +32


# one liner are fine for simple functions

def is_even(n) :
    """ Return True if n is even, False otherwise"""
    return n%2 == 0

# acessing doctring at runtime

# print(celcious_to_fehrenheit.__doc__)
print(is_even.__doc__)
help(is_even)
# help(celcious_to_fehrenheit)

print(increment.__doc__)
help(increment)

