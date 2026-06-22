# python error handling 


try:
    # Code that might raise an exception
    result = 10 / 0
except ZeroDivisionError:
    # Runs if the specific exception occurs
    print("Cannot divide by zero!")
else:
    # Runs ONLY if no exception occurred
    print(f"Result: {result}")
finally:
    # ALWAYS runs, exception or not
    print("Done.")

"""

try:
age = int(input("Enter age: "))
with open("data.txt") as f:
    content = f.read()

except ValueError:
    print("Age must be a number!")         # wrong input type

except FileNotFoundError:
    print("data.txt not found!")           # missing file

except (TypeError, AttributeError) as e:
    print(f"Type issue: {e}")              # multiple exceptions, one handler

except Exception as e:
    print(f"Unexpected error: {e}")        # catch-all (use sparingly)
"""

def set_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative.")   # raise built-in
    return age

# Custom exception
class InsufficientFundsError(Exception):
    def __init__(self, amount, balance):
        super().__init__(f"Need ₹{amount}, but balance is ₹{balance}")

def withdraw(amount, balance):
    if amount > balance:
        raise InsufficientFundsError(amount, balance)
    return balance - amount