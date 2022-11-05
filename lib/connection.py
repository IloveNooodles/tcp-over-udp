import socket

from .constant import DEFAULT_IP, DEFAULT_PORT, SEGMENT_SIZE, TIMEOUT
from .segment import Segment


class Connection:
    # TODO check if port already in used and check if port can be reused or set broadcast
    def __init__(
        self, ip: str = DEFAULT_IP, port: int = DEFAULT_PORT, is_server: bool = False
    ):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

        if is_server:
            print(f"[!] Server started at {ip}:{port}")

        else:
            print(f"[!] Client started at {ip}:{port}")

    def send_data(self, msg: Segment, dest: (str, int)):
        # Send single segment into destination
        self.socket.sendto(msg, dest)

    def listen_single_segment(self) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        self.socket.settimeout(TIMEOUT)
        self.socket.recvfrom(SEGMENT_SIZE)

    def close_socket(self):
        self.socket.close()
