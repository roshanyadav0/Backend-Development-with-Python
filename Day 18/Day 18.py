# 1. import vs from import vs import as

import math                    # imports the whole module
print(math.sqrt(16))          # must use module name as prefix

from math import sqrt          # imports only sqrt function
print(sqrt(16))               # use directly, no prefix needed

import numpy as np             # imports with an alias
print(np.array([1, 2, 3]))    # use alias as prefix

from math import sqrt as s     # alias on a specific function
print(s(16))


# 2. __name__ == '__main__' Guard

# greet.py

def greet(name):
    return f"Hello, {name}!"

print(__name__)   # prints '__main__' if run directly
                    # prints 'greet'   if imported by another file

if __name__ == '__main__':
    # This block ONLY runs when you execute this file directly
    # It is SKIPPED when this file is imported as a module
    print(greet("Alice"))


#    4. sys.path — How Python Finds Modules

import sys

print(sys.path)
# A list of directories Python searches when you do `import`
# ['', '/usr/lib/python3.x', '/usr/lib/python3.x/lib-dynload', ...]
# '' (empty string)  →  current working directory  ← checked FIRST
# /usr/lib/python3.x →  standard library
# site-packages/     →  third-party packages (pip installs)

# You can add custom paths at runtime:
sys.path.append('/my/custom/folder')
import my_custom_module            # Python will now find it there

"""
5. Big Picture — How It All Connects
your_project/
│
├── main.py          ← runs directly, __name__ == '__main__'
├── utils.py         ← a module, __name__ == 'utils' when imported
│
└── mypackage/       ← a PACKAGE (folder with __init__.py)
    ├── __init__.py  ← makes it a package
    └── helpers.py
    
python# Importing from a package
from mypackage import helpers
from mypackage.helpers import some_function

"""