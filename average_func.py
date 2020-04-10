def cal_average(num):
    sum_num = 0
    for n in num:
        sum_num = sum_num + n

    avg = sum_num / len(num)
    return avg
