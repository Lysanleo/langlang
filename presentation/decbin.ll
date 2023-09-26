x = input_int()

bin = 0
n = 2
cot = 0

while x>0:
    rem = 0
    quot = 0
    tmp = x
    # 计算 x = nq + r中的q与r
    while tmp > -1:
        if tmp == 1:
            rem = 1
        if tmp == 0:
            rem = 0
        tmp = tmp - n
        if tmp >= 0:
            quot = quot + 1

    # 计算 x = q
    x = quot
    
    # 计算 bin = r*2^cot + bin
    new_bit = 1
    if rem == 0:
        bin = bin
    else:
        if cot == 0:
            new_bit = rem
        else:
            mul = 1
            cot1 = 0
            while cot1 < cot:
                j = 0
                tmp1 = mul
                while j < 9:
                    mul = mul + tmp1
                    j = j + 1
                cot1 = cot1 + 1
            new_bit = mul
        bin = bin + new_bit
    cot = cot + 1
    # print(quot, x)

print(bin)
