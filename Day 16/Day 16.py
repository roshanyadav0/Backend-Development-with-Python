# python comprehensions

# list comprehensions

# Syntax: [expression for item in iterable if condition]

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Basic
squares = [n ** 2 for n in numbers]
# [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

# With condition (filter)
evens = [n for n in numbers if n % 2 == 0]
# [2, 4, 6, 8, 10]

# With transformation + condition
even_squares = [n ** 2 for n in numbers if n % 2 == 0]
# [4, 16, 36, 64, 100]

# if/else inside (ternary — note: condition goes in expression, not filter)
labels = ["even" if n % 2 == 0 else "odd" for n in numbers]
# ['odd', 'even', 'odd', 'even', ...]

# Dict comprehensions

# Syntax: {key: value for item in iterable if condition}

names = ["alice", "bob", "charlie"]

# Basic
name_lengths = {name: len(name) for name in names}
# {'alice': 5, 'bob': 3, 'charlie': 7}

# From two lists (zip)
prices = [250, 180, 320]
items = ["lunch", "coffee", "dinner"]
price_map = {item: price for item, price in zip(items, prices)}
# {'lunch': 250, 'coffee': 180, 'dinner': 320}

# Filter: only expensive items
costly = {item: price for item, price in zip(items, prices) if price > 200}
# {'lunch': 250, 'dinner': 320}

# Invert a dict (swap keys/values)
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
# {1: 'a', 2: 'b', 3: 'c'}


# Set comprehensions 

# Syntax: {expression for item in iterable if condition}

words = ["apple", "banana", "avocado", "blueberry", "cherry", "apricot"]

# Unique first letters
first_letters = {w[0] for w in words}
# {'a', 'b', 'c'}  — order not guaranteed

# Unique lengths, only long words
long_word_lengths = {len(w) for w in words if len(w) > 5}
# {6, 8, 9}

# Remove duplicates from a list (via set comprehension)
tags = ["food", "travel", "food", "bills", "travel"]
unique_tags = {tag.lower() for tag in tags}
# {'food', 'travel', 'bills'}

# Nested Comprehensions (Use Sparingly)


# Flatten a 2D list
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [n for row in matrix for n in row]
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Read as: "for each row, for each n in that row"

# 2D grid (nested output — a list of lists)
grid = [[r * c for c in range(1, 4)] for r in range(1, 4)]
# [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

# Rule: if you need 3+ levels, use a regular loop instead