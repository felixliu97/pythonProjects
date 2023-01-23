# write a function to calculate crc32 of a string and store it into a dictionary

import binascii

def calculate_crc32(string):
    crc32_dict = {}
    crc32 = binascii.crc32(string.encode('utf-8')) & 0xffffffff
    crc32_dict[string] = hex(crc32)
    return crc32_dict
    
print(calculate_crc32("Hello World"))