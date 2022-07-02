from unittest import result


nums1 = [2,3,5]
nums2 = [7,6,3]

def add_numbers(nums1, nums2):
    result = []
    sum, carry = 0, 0

    while nums1 or nums2:
        n1 = nums1.pop(0) if len(nums1) > 0 else 0
        n2 = nums2.pop(0) if len(nums2) > 0 else 0
        sum = n1 + n2 + carry
        carry = 0 if sum < 10 else sum / 10
        bit = sum % 10
        result.append(bit)
    
    print(result)

add_numbers(nums1, nums2)