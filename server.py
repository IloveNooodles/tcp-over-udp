import argparse
from os.path import isfile

import lib.segment as segment
from lib.connection import Connection
from lib.segment import Segment


class Server:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Server for handling file transfer connection to client"
        )
        parser.add_argument(
            "broadcast_port",
            metavar="[broadcast port]",
            type=int,
            help="broadcast port used for all client",
        )
        parser.add_argument(
            "pathfile_input",
            metavar="[Path file input]",
            type=str,
            help="path to file you want to send",
        )
        args = parser.parse_args()
        broadcast_port, pathfile_input = args.broadcast_port, args.pathfile_input

        self.broadcast_port = broadcast_port
        self.pathfile = pathfile_input

        if not self.file_exists():
            print("[!] Source file doesn't exists. Exiting...")
            exit(1)

        self.conn = Connection(is_server=True)
        data, filesize = self.get_filedata()
        self.data = data
        self.filesize = filesize
        self.filename = self.get_filename()
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")

    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients.")
        while True:
            self.conn.listen_single_segment()
            self.get_filename()

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr: (str, int)):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: (str, int)) -> bool:
        # Three way handshake, server-side, 1 client
        pass

    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]

        return self.pathfile.split("\\")[-1]

    def get_filedata(self):
        file = open(f"{self.pathfile}", "rb")
        data = file.read()
        filesize = len(data)
        file.close()
        return data, filesize

    def file_exists(self):
        return isfile(self.pathfile)


if __name__ == "__main__":
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()
