import socket

from .constant import DEFAULT_IP, DEFAULT_PORT, SEGMENT_SIZE, TIMEOUT
from .segment import Segment


class Connection:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

    def send_data(
        self, msg: Segment, dest: ("ip", "port") = (DEFAULT_IP, DEFAULT_PORT)
    ):
        # Send single segment into destination
        self.socket.sendto(msg, dest)

    def listen_single_segment(self) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        self.socket.settimeout(TIMEOUT)
        self.socket.recvfrom(SEGMENT_SIZE)

    def close_socket(self):
        self.socket.close()
