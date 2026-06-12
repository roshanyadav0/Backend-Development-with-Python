text = str(input("Enter a string: "))
list = text.split()
dict = {}

for word in list:
    if word in dict:
        dict[word] += 1
    else:
        dict[word] = 1

print(dict)