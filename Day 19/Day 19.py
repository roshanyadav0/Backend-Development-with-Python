"""  1. Package Directory Structure

my_project/
│
├── main.py                  ← entry point
│
└── expense_tracker/         ← your PACKAGE (folder)
    ├── __init__.py          ← makes it a package (can be empty or not)
    ├── models.py            ← Expense class / data structures
    ├── utils.py             ← helper functions
    ├── storage.py           ← file read/write
    └── reports.py           ← summaries, totals    

"""
    
# 3. Relative vs Absolute Imports python
# ── Absolute import (from project root) ──────────────────────────
from expense_tracker.models import Expense      # full path
from expense_tracker.utils  import format_currency

# ── Relative import (from within the package) ────────────────────
# Inside expense_tracker/reports.py:

from .models  import Expense          # . = current package
from .utils   import format_currency  # . = same folder
from ..other  import something        # .. = one level up (sub-packages)

# 4. Standard Library Exploration  

# datetime

from datetime import datetime, date, timedelta

now   = datetime.now()
today = date.today()

print(now.strftime("%d-%m-%Y %H:%M"))   # 27-06-2026 14:30
print(today)                            # 2026-06-27

# Arithmetic
week_later = today + timedelta(days=7)
diff = datetime(2026, 12, 31) - datetime.now()
print(f"{diff.days} days until New Year")

# os

import os

print(os.getcwd())                    # current working directory
print(os.listdir('.'))               # files in current folder
os.makedirs('data/logs', exist_ok=True)  # create nested dirs safely
print(os.environ.get('HOME'))        # read environment variable
print(os.path.join('data', 'expenses.json'))  # safe path building

# sys

import sys

print(sys.version)         # Python version info
print(sys.platform)        # 'linux', 'win32', 'darwin'
print(sys.argv)            # command-line arguments  ['main.py', 'arg1']
sys.exit(0)                # exit the program (0 = success)

# pathlib ← modern, preferred over os.path
from pathlib import Path

p = Path('data/expenses.json')

print(p.parent)        # data
print(p.name)          # expenses.json
print(p.stem)          # expenses
print(p.suffix)        # .json
print(p.exists())      # True / False

p.parent.mkdir(parents=True, exist_ok=True)   # create dirs
text = p.read_text()                          # read file
p.write_text('hello')                         # write file

# Glob — find all json files recursively
for f in Path('.').glob('**/*.json'):
    print(f)

