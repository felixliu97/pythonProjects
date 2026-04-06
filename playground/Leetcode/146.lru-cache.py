#
# @lc app=leetcode id=146 lang=python3
#
# [146] LRU Cache
#

# @lc code=start
class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.used = []
        self.cache = {}

    def get(self, key: int) -> int:
        if key in self.cache:
            self.used.remove(key)
            self.used.append(key)
            return self.cache[key]
        return -1

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache[key] = value
            self.used.remove(key)
            self.used.append(key)
        else:
            if len(self.used) == self.capacity:
                lru = self.used.pop(0)
                del self.cache[lru]
                self.cache[key] = value
                self.used.append(key)
            else:
                self.cache[key] = value
                self.used.append(key)


# Your LRUCache object will be instantiated and called as such:
# obj = LRUCache(capacity)
# param_1 = obj.get(key)
# obj.put(key,value)
# @lc code=end

