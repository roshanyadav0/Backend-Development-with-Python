# 1. Create & Activate a Virtual Environment

"""
# In your terminal (not Python file)

# Create venv
python -m venv myenv

# Activate (Linux/Mac)
source myenv/bin/activate

# Activate (Windows)
myenv\Scripts\activate

# Your prompt changes to:
# (myenv) $   ← you're now inside the venv

# Deactivate when done
deactivate

"""

# 2. pip install — Installing Packages

"""
# Install a package (only goes into THIS venv)
pip install requests

# Install a specific version
pip install requests==2.28.0

# Install multiple
pip install flask pandas numpy

# Upgrade a package
pip install --upgrade requests

# Uninstall
pip uninstall requests

"""
# 3. pip freeze — See What's Installed

"""
# Lists all installed packages + exact versions
pip freeze

# Output looks like:
# certifi==2023.7.22
# charset-normalizer==3.3.0
# idna==3.4
# requests==2.28.2
# urllib3==1.26.18

"""

# 4. requirements.txt — Create & Use

""" 
# ── CREATING ──────────────────────────────────────
# Save your environment's packages to a file
pip freeze > requirements.txt

# requirements.txt now contains:
# requests==2.28.2
# flask==2.3.3
# pandas==2.1.0
# ...


# ── USING (on another machine or teammate's PC) ───
# First, create + activate a fresh venv, then:
pip install -r requirements.txt
# Installs every package at the exact pinned version

"""
# 5. Proper Project Setup (Full Workflow)

"""
my_project/
│
├── myenv/              ← venv folder (NEVER commit this)
├── main.py
├── utils.py
├── requirements.txt    ← commit this ✅
└── .gitignore          ← add myenv/ here ✅

# .gitignore — exclude the venv folder
myenv/
__pycache__/
*.pyc

# Full project setup from scratch:

mkdir my_project && cd my_project   # 1. Create folder
python -m venv myenv                # 2. Create venv
source myenv/bin/activate           # 3. Activate it
pip install flask requests          # 4. Install packages
pip freeze > requirements.txt       # 5. Save dependencies
# ... write your code ...
deactivate                          # 6. Deactivate when done

Your System Python          venv (myenv/)
─────────────────          ──────────────────────────
python 3.11                python 3.11  ← own copy
pip                        pip          ← own copy
site-packages/             site-packages/
    (global, shared)           requests==2.28  ← isolated!
                            flask==2.3.3

"""
