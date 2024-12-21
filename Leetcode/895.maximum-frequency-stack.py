#
# @lc app=leetcode id=895 lang=python3
#
# [895] Maximum Frequency Stack
#
from collections import defaultdict
# @lc code=start
class FreqStack:

    def __init__(self):
        self.freq_map = defaultdict(int)
        self.stack_map = defaultdict(list)
        self.max_freq = 0

    def push(self, val: int) -> None:
        self.freq_map[val] += 1
        freq = self.freq_map[val]
        self.stack_map[freq].append(val)
        self.max_freq = max(self.max_freq, freq)

    def pop(self) -> int:
        val = self.stack_map[self.max_freq].pop()
        self.freq_map[val] -= 1
        if not self.stack_map[self.max_freq]:
            del self.stack_map[self.max_freq]
            self.max_freq -= 1
        return val
        


# Your FreqStack object will be instantiated and called as such:
# obj = FreqStack()
# obj.push(val)
# param_2 = obj.pop()
# @lc code=end

