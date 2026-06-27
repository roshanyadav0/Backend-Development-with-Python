# main.py  ← consumes your module

import utils                        # import whole module
from utils import greet, PI         # import specific names
import utils as u                   # import with alias

print(utils.add(10, 5))            # 15
print(greet("Alice"))              # Hello, Alice!
print(PI)                          # 3.14159
print(u.add(1, 2))                 # 3