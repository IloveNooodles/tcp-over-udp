import binascii

from .constant import CRC_INIT, CRC_POLYNOM

"""
CRC16 Polynomial
x16 + x12 + x5  + 1
1 0001 0000 0010 0001 & 0xFFFF
0x 1    0    2    1
0x1021
"""


class CRC16:
    def __init__(self, data: bytes):
        self.data = data
        self.len = len(data)

    def calculate(self):
        crc16 = CRC_INIT
        for byte in self.data:
            byte_to_calc = byte
            for i in range(8):
                """
                CRC-16/CCITT Uses big endian
                Shift left 1 by 1
                make sure to work on 16 bit
                """
                # MSB check changes because need to check bit 15 instead of 7
                msb_crc = (crc16 & 0x8000) >> 8
                msb_byte = byte_to_calc & 0x80
                msb_is_set = msb_byte ^ msb_crc
                crc16 = (crc16 << 1) & 0xFFFF
                if msb_is_set:
                    crc16 = crc16 ^ CRC_POLYNOM

                byte_to_calc = (byte_to_calc << 1) & 0xFF

        return crc16 & 0xFFFF


if __name__ == "__main__":
    data = b"hello world"
    crc16 = CRC16(data)
    crc32_res = crc16.calculate()
    assert crc32_res == binascii.crc_hqx(data, CRC_INIT)
    print(f"CRC16: {hex(crc32_res)}, binascii: {hex(binascii.crc_hqx(data, 0xFFFF))}")
