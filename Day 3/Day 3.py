# append and extend 

fruits = ['seb', 'kela']

fruits.append('aam')

print(fruits)

fruits.extend(['angoor','tarbuj'])
print(fruits)

# pop and remove

nums = [1,2,3,4,5]

nums.pop()
print(nums)
nums.pop(1)
print(nums)

nums.remove(3)
print(nums)

fruits.remove('kela')
print(fruits)

# SORT  AND REVERSE 
num = [5,4,3,2,1,3,4,2,1,3,1,6]
num.sort()
print(num)
num.reverse()
print(num)

#   other useful list methods

print(num.count(1))
print(num.index(5))
print(num.insert(35,355))
print(num)
print(nums.clear())
print(nums)
print(len(num))


# slicing
# list[start : stop : step]
a = [0, 10, 20, 30, 40, 50, 60, 70]

a[2:5]      # [20, 30, 40]  start incl, stop excl
a[:3]       # [0, 10, 20]   from beginning
a[5:]       # [50, 60, 70]  to end
a[::]        # full copy
a[::2]      # [0, 20, 40, 60]  every 2nd
a[::-1]     # [70,60,...,0]  reversed!
a[-3:]      # [50, 60, 70]  last 3

# tuples

t = 1,2,3,4,5
print(type(t))
t = (1,2,3,4,5)
print(type(t))

print(t[0])

# unpacking tuples

a,b,*c = t
print(a)
print(b)        
print(c)
a = 4
print(type(a))
a = tuple(c)
print(type(a))
print(a)

# nexted lists 

# 2D list
matrix = [
    [1,2,3],
    [4,5,6],
    [7,8,9]
]

for row in matrix:
    for element in row:
        print(element, end=' ')
    print()


# flatten with list comprehension
flat = [cell for row in matrix for cell in row] 
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

# column extraction
col2 = [row[2] for row in matrix] # this means [place which you want to extract next write the loop for row in matrix]
# [3, 6, 9]

# tic tac toe board game

board = [
    ['X', 'O', 'X'], 
    ['O', 'X', 'O'], 
    ['O', 'X', 'X']
]

for row in board:
    print('|'.join(row))
