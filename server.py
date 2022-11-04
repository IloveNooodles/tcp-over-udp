import argparse

import lib.connection
import lib.segment as segment
from lib.segment import Segment


class Server:
    def __init__(self):
        # Init server
        pass

    def listen_for_clients(self):
        # Waiting client for connect
        pass

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr: ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: ("ip", "port")) -> bool:
        # Three way handshake, server-side, 1 client
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Server for handling file transfer connection to client"
    )
    parser.add_argument(
        "integers",
        metavar="[broadcast port]",
        type=int,
        help="broadcast port used for all client",
    )
    parser.add_argument(
        "strings",
        metavar="[Path file input]",
        type=str,
        help="path to file you want to send",
    )
    args = parser.parse_args()
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()
