# Open() Modes
open("file.txt", "r") # Read  (Default) file must exist
open("file.txt", "w") # Write Create or overrite
open("file.txt", "a") # append - add to end
open("file.txt", "rb")  # read binary - for images, PDF's ,etc.


# The with statement and WHY

# ❌ Without with — you must close manually (easy to forget)

f = open("file.txt", "r")
data = f.read()
f.close()  # skipped if an error occurs above = resource leak

# ✅ With with — auto-closes even if an error occurs

with open("file.txt" , "r") as f :
    data = f.read()

# ── WRITE ──────────────────────────────────────
with open("notes.txt", "w") as f:
    f.write("Hello\n")
    f.writelines(["Line 2\n", "Line 3\n"])  # write a list

# ── READ ───────────────────────────────────────
with open("notes.txt", "r") as f:
    content = f.read()        # entire file as one string
    # f.readline()            # one line at a time
    # f.readlines()           # list of lines

# ── APPEND ─────────────────────────────────────
with open("notes.txt", "a") as f:
    f.write("Line 4\n")       # doesn't erase existing content


# os.path File checking 

import os

os.path.exists("notes.txt")   # True / False — file or folder exists
os.path.isfile("notes.txt")   # True only for files
os.path.isdir("myfolder")     # True only for directories
os.path.getsize("notes.txt")  # size in bytes

# Safe pattern — read only if file exists
if os.path.isfile("notes.txt"):
    with open("notes.txt", "r") as f:
        print(f.read())
else:
    print("File not found")


