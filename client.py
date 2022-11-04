import argparse

import lib.connection
import lib.segment as segment
from lib.segment import Segment


class Client:
    def __init__(self):
        # Init client
        pass

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        pass

    def listen_file_transfer(self):
        # File transfer, client-side
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Server for handling file transfer connection to client"
    )
    parser.add_argument(
        "integers",
        metavar="[client port]",
        type=int,
        help="client port to start the service",
    )
    parser.add_argument(
        "integers",
        metavar="[broadcast port]",
        type=int,
        help="broadcast port used for destination address",
    )
    parser.add_argument(
        "strings",
        metavar="[path file output]",
        type=str,
        help="output path location",
    )
    args = parser.parse_args()
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
