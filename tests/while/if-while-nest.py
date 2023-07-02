i = 0

while i < 10:
    j = 0
    while j < i:
        if j + j == i:
            print(i)
            j = i
        else:
            j = j + 1
    i = i + 1