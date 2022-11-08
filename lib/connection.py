import socket
from time import time
from typing import Tuple

from .constant import (DEFAULT_BROADCAST_PORT, DEFAULT_IP, DEFAULT_PORT,
                       SEGMENT_SIZE, TIMEOUT)
from .segment import Segment


class Connection:
    # TODO check if port already in used and check if port can be reused or set broadcast
    def __init__(
        self, ip: str = DEFAULT_IP, broadcast_port: int = DEFAULT_BROADCAST_PORT, port: int = DEFAULT_PORT, is_server: bool = False
    ):
        if is_server:
            self.ip = ip
            self.port = broadcast_port
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((ip, broadcast_port))
            print(f"[!] Server started at {self.ip}:{self.port}")
        else:
            self.ip = ip
            self.port = broadcast_port
            self.client_port = port
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((ip, port))
            print(f"[!] Client started at {self.ip}:{self.port}")

    def send_data(self, msg: Segment, dest: Tuple[str, int]):
        self.socket.sendto(msg, dest)

    def listen_single_segment(self) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        try:
            self.socket.settimeout(TIMEOUT)
            return self.socket.recvfrom(SEGMENT_SIZE)
        except TimeoutError as e:
            raise e

    def close_socket(self):
        self.socket.close()

    def __str__(self):
        print (f"ip: {self.ip}\n broadcast_port: {self.port}\n  client port:{self.client_port}\n")