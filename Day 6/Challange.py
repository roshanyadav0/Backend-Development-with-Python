# Challange Fizz Buzz using function

def one_to_hundred (a) :
    for i in range(1,a+1) :
        if i % 3 == 0 and i % 5 == 0 :
            print("Fizz Buzz")
        elif i % 3 == 0 :
            print("Fizz Buzz")
        elif i % 5 == 0 :
            print("Fizz Buzz")
        else :
            print(f"{i} is not a Fuzz Buzz")

one_to_hundred(int(input("Please give input count till hundred :")))