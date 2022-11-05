import argparse

import lib.segment as segment
from lib.connection import Connection
from lib.segment import Segment


class Client:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Server for handling file transfer connection to client"
        )
        parser.add_argument(
            "client_port",
            metavar="[client port]",
            type=int,
            help="client port to start the service",
        )
        parser.add_argument(
            "broadcast_port",
            metavar="[broadcast port]",
            type=int,
            help="broadcast port used for destination address",
        )
        parser.add_argument(
            "pathfile_output",
            metavar="[path file output]",
            type=str,
            help="output path location",
        )
        args = parser.parse_args()
        client_port, broadcast_port, pathfile_output = (
            args.client_port,
            args.broadcast_port,
            args.pathfile_output,
        )

        self.client_port = client_port
        self.broadcast_port = broadcast_port
        self.pathfile_output = pathfile_output
        self.conn = Connection()

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        print("[!] Initiating three way handshake...")
        pass

    def listen_file_transfer(self):
        # File transfer, client-side
        pass


if __name__ == "__main__":
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
