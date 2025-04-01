def get_playlists(videos, k, threshold):
    n = len(videos)
    results = []
    for i in range(n-k+1):
        over = [x for x in videos[i:i+k] if x > threshold]
        if len(over) == 0:
            results.append(videos[i:i+k])
    print(results)

videoLength = [3,1,5,6,8,2,1]
k=2
threshold = 5
get_playlists(videoLength,k,threshold)