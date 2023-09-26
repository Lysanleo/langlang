x = input_int()

i = 0

while i <= x:
    j = 0
    while j < i:
        if j + j == i:
            print(i)
            j = i
        else:
            j = j + 1
    # if j == 0 and i == 0:
    if i == 0:
        print(j)
    i = i + 1