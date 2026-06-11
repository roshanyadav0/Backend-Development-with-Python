value = float(input("Enter the value: "))
unit = input("Enter the unit (m, cm, mm, km): ")

if unit == 'm':
    converted_value = value * 100
    print(f"{value} m is equal to {converted_value} cm.")
elif unit == 'cm':
    converted_value = value / 100
    print(f"{value} cm is equal to {converted_value} m.")
elif unit == 'mm':
    converted_value = value / 1000
    print(f"{value} mm is equal to {converted_value} m.")   
elif unit == 'km':
    converted_value = value * 1000
    print(f"{value} km is equal to {converted_value} m.")   
else:
    print("Invalid unit. Please enter m, cm, mm, or km.")
