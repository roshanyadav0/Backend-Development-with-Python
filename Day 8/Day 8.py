# Python Decorators: Wrappers & functools.wraps

# First-class functions recap
def greet(name):
    return f"Hello, {name}"

say_hi = greet          # assign
say_hi("Alice")         # → "Hello, Alice"

def call_it(fn):        # pass as argument
    return fn("Bob")

call_it(greet)          # → "Hello, Bob"

# Writing a timer decorator

import time
import functools

def timer(func):
    @functools.wraps(func)          # preserves func's identity (see below)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)   # call the original
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f}s")
        return result
    return wrapper

@timer
def slow_add(a, b):
    time.sleep(0.1)
    return a + b

slow_add(3, 4)
# slow_add took 0.1002s
# → 7


# Writing a logger decorator
def logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Calling {func.__name__} with args={args} kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} returned {result}")
        return result
    return wrapper

@logger
def multiply(x, y):
    return x * y

multiply(3, 5)
# [LOG] Calling multiply with args=(3, 5) kwargs={}
# [LOG] multiply returned 15