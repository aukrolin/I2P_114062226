m = [6.15,7.095,8.355]
l = [1,4,8]
s = [66,60]
for i, val in enumerate(m):
    for j, t in enumerate(s):
        print(f'等級{l[i]} in {j} * 研究力（小） 僅出美模每秒虧損{(900/t-val)*30:.2f} 元')
    print("-----")