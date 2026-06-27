# utils.py  ← your reusable module

def add(a, b):
    return a + b

def greet(name):
    return f"Hello, {name}!"

PI = 3.14159

if __name__ == '__main__':
    # Quick self-test — only runs when you run utils.py directly
    print(add(2, 3))       # 5
    print(greet("Bob"))    # Hello, Bob!