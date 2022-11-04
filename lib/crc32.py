import binascii

from constant import CRC_CONSTANT

"""
CRC32 Polynomial
x32 + x26 + x23 + x22 + x16 + x12 + x11 + x10 + x8 + x7 + x5 + x4 + x2 + x + 1
    1 0000 0100 1100 0001 0001 1101 1011 0111
0x 01 04        C1        1D        B7
0x0104C11DB7 in little endian 0xEDB88320
"""


class CRC32:
    def __init__(self, data: bytes):
        self.data = data
        self.len = len(data)

    def calculate(self):
        crc32 = 0xFFFFFFFF
        for byte in self.data:
            byte_to_calc = byte
            for i in range(8):
                # Get MSB and shift right
                # Because little endian just do & 1
                # if msb then the xor occur else do nothing
                msb = (byte_to_calc ^ crc32) & 1
                crc32 = crc32 >> 1
                if msb:
                    crc32 = crc32 ^ CRC_CONSTANT

                byte_to_calc = byte_to_calc >> 1

        return (~crc32) & 0xFFFFFFFF


if __name__ == "__main__":
    data = b"hello world"
    crc32 = CRC32(data)
    crc32_res = crc32.calculate()
    assert binascii.crc32(data) == crc32_res
    print(f"Checksum of '{data.decode()}' is: {hex(crc32_res)}")
