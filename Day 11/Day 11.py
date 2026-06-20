# Revision from day 6 - day 10

# Day 6
# Functions 
# Dockstring

def sum_of_two(a = 49,b = 3) :
    """ This function prints sum 
        of two numbers . IF arguments are passed than sum of default numbers are 49 and 3 will pe returned.
    """
    return a+b

print(sum_of_two())
print(sum_of_two.__doc__)  # """ """  is used to give the document
help(sum_of_two)

# Day 7
# *args (Tuples)

def sum_of_list(*args) :
    return sum(args)

list = [3,56,3,75,3,75,4]
print(sum_of_list(*list))  # *list is unpacking into tuple

# **kwargs (Dictionary)
def print_key_values(**kwargs) :
    for a,b in kwargs.items() :
        print(f"{a} : {b}")

student_scores = {
    "Alice": 92,
    "Bob": 85,
    "Charlie": 78
}
print_key_values(**student_scores) # unpacking dictonary into keyward arguments

# default and pit fall
# default = def sum(a = 4,b = 0) 
# pitfall = def append_to(item, l = []) l = [] is pit fall default list

# Day 8
# decorators  a function which takes function and return wrapper function

def my_decorator(func):  # decorator function
    def wrapper(*args, **kwargs): # function which we will return and this the main work will be done  (ars and kwars is used to pass the arguments comes from main function which is called)
        print("Before calling the function")
        result = func(*args, **kwargs)
        print("After calling the function")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")


# functions.wrap whis is used to change the wapper__name__  = func__name__ which means it is used to copy documentations



# Day 9
# python has 2 diffrent artributes one is class and one is instance 
class Animal :
    list_of_animal = []
    
    def __init__(self,category,name,weight,sound):
        self.category = category # this is the instance attribute
        self.name = name
        self.weight = weight
        self.sound = sound

        Animal.list_of_animal.append(self) # This is how class attributes are called and updated

    def __repr__(self): # THis function is used to change the representation of the Object
        return f"Animal(category={self.category!r}, name={self.name!r}, weight={self.weight}, sound={self.sound!r})"
    
    def list_animals(self) :
        print(Animal.list_of_animal)


dog = Animal("Dog","Kalu",23.4,"Woof")
dog.list_animals()
print(dog)

# @classmethod is used to create function and functorn work on class 
# @staticmethod is used to directly provide value inside the function and self is not required in method argument


# Dunder methods which make object feel native in pythhon
#__repr__This is used to make user frendly representaion for developers
#__str__ THis is used to make user frendly represtanion for users
#__lt__ This is used to compare the instance 
#__eq__ This is used to check instance are equal or not


# Day 10
# super method
class Expense:
    def __init__(self, title, amount, category):
        self.title    = title
        self.amount   = float(amount)
        self.category = category

class ExpenseCategory(Expense):          # child
    def __init__(self, title, amount, category, budget):
        super().__init__(title, amount, category)   # runs Expense.__init__
        self.budget = float(budget)                 # child-only attribute
