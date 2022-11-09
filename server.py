from math import ceil
from typing import Tuple

from lib.argparse import Parser
from lib.connection import Connection
from lib.constant import (ACK_FLAG, PAYLOAD_SIZE, SEGMENT_SIZE, SYN_ACK_FLAG,
                          SYN_FLAG, WINDOW_SIZE)
from lib.segment import Segment


class Server:
    def __init__(self):
        args = Parser(is_server=True)
        broadcast_port, pathfile_input = args.broadcast_port, args.pathfile_input

        self.broadcast_port = broadcast_port
        self.pathfile = pathfile_input
        self.conn = Connection(broadcast_port=broadcast_port, is_server=True)
        data, filesize = self.get_filedata()
        self.data = data
        self.filesize = filesize
        self.segment = Segment()
        self.client_list = []
        self.filename = self.get_filename()
        self.seq = 0
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")

    def count_segment(self):
        return ceil(self.filesize / PAYLOAD_SIZE)

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
                    print("\nClient list:")
                    for index, (ip, port) in enumerate(self.client_list):
                        print(f"{index+1} {ip}:{port}")

                    print("")
                    break

            except TimeoutError:
                print("[!] Timeout Error")

    def start_file_transfer(self):
        for client in self.client_list:
            self.three_way_handshake(client)
            self.file_transfer(client)

    def file_transfer(self, client_addr: Tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        list_segment = []
        num_of_segment = self.count_segment()
        # After three way handshake seq num is now 1
        # Flags is 0 for sending data
        for i in range(num_of_segment):
            segment = Segment()
            data_to_set = self.data[i*PAYLOAD_SIZE:PAYLOAD_SIZE]
            segment.set_payload(data_to_set)
            header = segment.get_header()
            header['seq'] = self.seq
            header['ack'] = 0
            segment.set_header(header)
            list_segment.append(segment)
            self.seq += 1

        window_size = min(num_of_segment, WINDOW_SIZE)
        sb = 0

        while (sb < num_of_segment):
            size_slide = window_size
            for i in range(size_slide):
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending Segment {sb+i+1}")
                self.conn.send_data(list_segment[i+sb].get_bytes(), client_addr)
            for i in range(size_slide):
                try:
                    data, response_addr = self.conn.listen_single_segment()
                    segment = Segment()
                    segment.set_from_bytes(data)
                    if (client_addr[1] == response_addr[1] and segment.get_flag() == ACK_FLAG and segment.get_header()['ack'] == sb+1):
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved ACK {sb+1}")
                        sb += 1
                        window_size = min(num_of_segment - sb, WINDOW_SIZE)
                    elif (client_addr[1] != response_addr[1]):
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved ACK from wrong client")
                    elif (segment.get_flag() != ACK_FLAG):
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved wrong flag")
                    else:
                        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved Wrong ACK")
                except:
                    print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending prev seq num")
        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] File transfer complete")
        sendFIN = Segment()
        sendFIN.set_flag(['FIN'])
        self.conn.send_data(sendFIN.get_bytes(), client_addr)

    def three_way_handshake(self, client_addr: Tuple[str, int]) -> bool:
        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Initiating three way handshake...")
        self.segment.set_flag(['SYN'])
        while True:
            # SYN
            if self.segment.get_flag() == SYN_FLAG:
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending SYN")
                header = self.segment.get_header()
                header["seq"] = self.seq
                header["ack"] = 0
                self.conn.send_data(self.segment.get_bytes(), client_addr)
                try:
                    data, address = self.conn.listen_single_segment()
                    self.segment.set_from_bytes(data)
                    self.seq += 1

                except TimeoutError:
                    print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending SYN")
            
            # ACK only send ack to client no need to add seq num
            elif self.segment.get_flag() == SYN_ACK_FLAG:
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieve SYN-ACK")
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending ACK")
                header = self.segment.get_header()
                header["ack"] = header['seq']
                self.segment.set_header(header)
                self.segment.set_flag(["ACK"])
                self.conn.send_data(self.segment.get_bytes(), client_addr)
                break
  
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
