import socket
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        # Init UDP socket
        pass

    def send_data(self, msg : Segment, dest : ("ip", "port")):
        # Send single segment into destination
        pass

    def listen_single_segment(self) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        pass

    def close_socket(self):
        # Release UDP socket
        pass
