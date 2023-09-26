x = input_int()

i = x
j = i - 1
cot1 = x
fact = i
while i > 0:
    cot2 = j
    tmp = fact
    while cot2 > 1:
        fact = fact + tmp
        cot2 = cot2 - 1
    j = j - 1
    i = i - 1

print(fact)
