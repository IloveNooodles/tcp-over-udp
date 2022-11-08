from typing import Tuple
from math import ceil
from lib.argparse import Parser
from lib.connection import Connection
from lib.segment import Segment


class Server:
    def __init__(self):
        args = Parser(is_server=True)
        broadcast_port, pathfile_input = args.broadcast_port, args.pathfile_input

        self.broadcast_port = broadcast_port
        self.pathfile = pathfile_input
        self.conn = Connection(broadcast_port=broadcast_port, is_server=True)
        data, filesize = self.get_filedata()
        self.segment = Segment()
        self.segment.set_payload(data)
        self.filesize = filesize
        self.client_list = []
        self.filename = self.get_filename()
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")
    
    def countSegment(self):
        return ceil(self.filesize/32768)

    # TODO kalo ngelebihin segment 2**15, dipecah datanya jadi 2 nanti dikirim2 sampe fin flag
    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients.")
        while True:
            try:
                client = self.conn.listen_single_segment()
                client_address = client[1]
                ip, port = client_address
                self.client_list.append(client_address)
                print(f"[!] Recieved request from {ip}:{port}")
                choice = input("[?] Listen more (y/n) ").lower()
                while not self.choice_valid(choice):
                    print("[!] Please input correct input")
                    choice = input("[?] Listen more (y/n) ").lower()

                if choice == 'n':
                    print("Client list:")
                    for index, (ip, port) in enumerate(self.client_list):
                        print(f"{index+1} {ip}:{port}")

                    break

            except TimeoutError:
                print(f"[!] Timeout Error")

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        for client in self.client_list:
            self.three_way_handshake(client)
            # self.file_transfer(client)
        pass

    def file_transfer(self, client_addr: Tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: Tuple[str, int]) -> bool:
        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Initiating three way handshake...")
        self.conn.send_data(self.segment.get_bytes(), client_addr)
        pass

    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]

        elif "\\" in self.pathfile:
            return self.pathfile.split("\\")[-1]
        
        return self.pathfile

    def get_filedata(self):
        try:
            file = open(f"{self.pathfile}", "rb")
            data = file.read()
            filesize = len(data)
            file.close()
            return data, filesize
        except FileNotFoundError:
            print(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)

    def choice_valid(self, choice: str):
        if choice.lower() == 'y':
            return 'y'
        elif choice.lower() == 'n':
            return 'n'
        else:
            return False

if __name__ == "__main__":
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()
