stockPrices = [5,3,5,7,8]
k = 3

def getintervals(prices, k):
    if k == 1:
        return len(prices)
    intervals = 0
    for i in range(len(stockPrices) - k + 1):
        window = prices[i:i+k]
        print(i, window)
        increasing = True
        for j in range(1, k):
            if window[j] <= window[j-1]:
                increasing = False
                break
        if increasing:
            print("This wondow is increasing")
            intervals += 1
    print(f"intervals:{intervals}")
    return intervals

getintervals(stockPrices, k)