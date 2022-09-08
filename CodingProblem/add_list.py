import unittest

def add_numbers(nums1, nums2):
    result = []
    sum, carry = 0, 0

    while nums1 or nums2:
        n1 = nums1.pop(0) if len(nums1) > 0 else 0
        n2 = nums2.pop(0) if len(nums2) > 0 else 0
        sum = n1 + n2 + carry
        carry = 0 if sum < 10 else sum // 10
        bit = sum % 10
        result.append(bit)

    if carry > 0:
        result.append(carry)
    
    return result

class TestAddNumbers(unittest.TestCase):
    def test_1(self):
        actual = add_numbers([2,3,5],[7,6,3])
        expected = [9,9,8]
        self.assertEqual(actual, expected)

    def test_2(self):
        actual = add_numbers([2,3],[7,6,3])
        expected = [9,9,3]
        self.assertEqual(actual, expected)

    def test_3(self):
        actual = add_numbers([],[7,6,3])
        expected = [7,6,3]
        self.assertEqual(actual, expected)

    def test_4(self):
        actual = add_numbers([],[])
        expected = []
        self.assertEqual(actual, expected)

    def test_5(self):
        actual = add_numbers([1,0,9],[9,2,3])
        expected = [0,3,2,1]
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()