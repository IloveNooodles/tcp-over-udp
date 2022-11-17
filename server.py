import threading
import time
import os

from math import ceil
from socket import timeout as socket_timeout
from typing import Dict, List, Tuple

from lib.argparse import Parser
from lib.connection import Connection
from lib.constant import (ACK_FLAG, FIN_ACK_FLAG, PAYLOAD_SIZE, SEGMENT_SIZE,
                          SYN_ACK_FLAG, SYN_FLAG, TIMEOUT_LISTEN, WINDOW_SIZE)
from lib.segment import Segment


class Server:
    def __init__(self):
        args = Parser(is_server=True)
        broadcast_port, pathfile_input = args.get_values()
        self.broadcast_port: str = broadcast_port
        self.pathfile: str = pathfile_input
        self.conn = Connection(broadcast_port=broadcast_port, is_server=True)
        self.file = self.open_file()
        self.filesize = self.get_filesize()
        self.segment = Segment()
        self.client_list: List[Tuple[int, int]] = []
        self.filename = self.get_filename()
        self.is_parallel = False
        self.breakdown_file()
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")

    def count_segment(self):
        return ceil(self.filesize / PAYLOAD_SIZE)

    def always_listen(self):
        self.all_clients: Dict[Tuple[str, int], List[Segment]] = {}
        while True:
            try:
                client = self.conn.listen_single_segment(10)
                client_address = client[1]
                ip, port = client_address
                if (client_address not in self.all_clients):
                    print(f"[!] Received request from {ip}:{port}")
                    self.all_clients[client_address] = []
                    new_transfer = threading.Thread(target=self.start_file_transfer, kwargs={
                                                    "client_parallel": client_address})
                    new_transfer.start()
                else:  # connection already established
                    self.all_clients[client_address].append(client[0])
            except socket_timeout:
                print("[!] Timeout Error for listening client. exiting")
                exit(0)

    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients.")
        while True:
            if (self.is_parallel):
                self.always_listen()
            else:
                try:
                    client = self.conn.listen_single_segment(TIMEOUT_LISTEN)
                    client_address = client[1]
                    ip, port = client_address
                    self.client_list.append(client_address)
                    print(f"[!] Received request from {ip}:{port}")
                    choice = input("[?] Listen more (y/n) ").lower()
                    while not self.choice_valid(choice):
                        print("[!] Please input correct input")
                        choice = input("[?] Listen more (y/n) ").lower()
                    if choice == "n":
                        print("\nClient list:")
                        for index, (ip, port) in enumerate(self.client_list):
                            print(f"{index+1} {ip}:{port}")
                        print("")
                        break
                except socket_timeout:
                    print("[!] Timeout Error for listening client. exiting")
                    break

    def start_file_transfer(self, client_parallel=None):
        if not self.is_parallel:
            for client in self.client_list:
                self.three_way_handshake(client)
                # self.send_metadata(client)
                self.file_transfer(client)
        else:
            self.three_way_handshake(client_parallel)
            # self.send_metadata(client_parallel)
            self.file_transfer(client_parallel)

    def breakdown_file(self):
        self.list_segment: List[Segment] = []

        metadata_segment = Segment()
        filename = self.get_name_part()
        extension = self.get_extension_part()
        filesize = self.filesize
        metadata = filename.encode() + ",".encode() + extension.encode() + \
            ",".encode() + str(filesize).encode()
        metadata_segment.set_payload(metadata)
        header = metadata_segment.get_header()
        header["seq"] = 2
        header["ack"] = 0
        metadata_segment.set_header(header)
        self.list_segment.append(metadata_segment)

        num_of_segment = self.count_segment()
        # After three way handshake seq num is now 1
        # Flags is 0 for sending data
        for i in range(num_of_segment):
            segment = Segment()
            data_to_set = self.get_filechunk(i)
            segment.set_payload(data_to_set)
            header = segment.get_header()
            header["seq"] = i + 3
            header["ack"] = 3
            segment.set_header(header)
            self.list_segment.append(segment)

    def file_transfer(self, client_addr: Tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        # Sequence number 0 for SYN
        # Sequence number 1 for ACK
        # Sequence number 2 for Metadata
        num_of_segment = len(self.list_segment) + 2
        window_size = min(num_of_segment, WINDOW_SIZE)
        sequence_base = 2
        reset_conn = False
        while sequence_base < num_of_segment and not reset_conn:
            sequence_max = window_size
            for i in range(sequence_max):
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending Segment {sequence_base + i}"
                )
                if i + sequence_base < num_of_segment:
                    self.conn.send_data(
                        self.list_segment[i + sequence_base -
                                          2].get_bytes(), client_addr
                    )
            for i in range(sequence_max):
                try:
                    data, response_addr = self.get_answer(client_addr)
                    segment = Segment()
                    segment.set_from_bytes(data)

                    if (
                        client_addr[1] == response_addr[1]
                        and segment.get_flag() == ACK_FLAG
                        and segment.get_header()["ack"] == sequence_base + 1
                    ):
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received ACK {sequence_base + 1}"
                        )
                        sequence_base += 1
                        window_size = min(
                            num_of_segment - sequence_base, WINDOW_SIZE)
                    elif client_addr[1] != response_addr[1]:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received ACK from wrong client"
                        )
                    elif segment.get_flag() != ACK_FLAG:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved Wrong Flag, resetting connection"
                        )
                        reset_conn = True

                    else:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received Wrong ACK"
                        )
                        request_number = segment.get_header()["ack"]
                        sequence_max = (
                            sequence_max - sequence_base) + request_number
                        sequence_base = request_number
                except:
                    print(
                        f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending prev seq num"
                    )
        if reset_conn:
            self.three_way_handshake(client_addr)
            self.send_metadata(client_addr)
            self.file_transfer(client_addr)
        else:
            print(
                f"[!] [Client {client_addr[0]}:{client_addr[1]}] File transfer complete, sending FIN..."
            )
            sendFIN = Segment()
            sendFIN.set_flag(["FIN"])
            self.conn.send_data(sendFIN.get_bytes(), client_addr)
            is_ack = False

            # Wait for ack
            while not is_ack:
                try:
                    data, response_addr = self.get_answer(client_addr)
                    segment = Segment()
                    segment.set_from_bytes(data)
                    if (
                        client_addr[1] == response_addr[1]
                        and segment.get_flag() == FIN_ACK_FLAG
                    ):
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved FIN-ACK"
                        )
                        sequence_base += 1
                        is_ack = True
                        if (self.is_parallel):
                            self.all_clients.pop(client_addr)
                except socket_timeout:
                    print(
                        f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending FIN"
                    )
                    self.conn.send_data(sendFIN.get_bytes(), client_addr)

            # send ACK and tear down connection
            print(
                f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending ACK Tearing down connection."
            )
            segmentACK = Segment()
            segmentACK.set_flag(["ACK"])
            self.conn.send_data(segmentACK.get_bytes(), client_addr)

    def get_answer(self, client_addr: Tuple[str, int]):
        if (self.is_parallel):
            time_timeout = time.time() + 1
            while (time.time() < time_timeout):
                if len(self.all_clients[client_addr]) > 0:
                    return (self.all_clients[client_addr].pop(0), client_addr)
            raise socket_timeout
        else:
            return self.conn.listen_single_segment()

    def three_way_handshake(self, client_addr: Tuple[str, int]) -> bool:
        print(
            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Initiating three way handshake..."
        )
        self.segment.set_flag(["SYN"])
        while True:
            # SYN
            if self.segment.get_flag() == SYN_FLAG:
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending SYN")
                header = self.segment.get_header()
                header["seq"] = 0
                header["ack"] = 0

                self.conn.send_data(self.segment.get_bytes(), client_addr)
                try:
                    data, _ = self.get_answer(client_addr)
                    self.segment.set_from_bytes(data)

                except socket_timeout:
                    print(
                        f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending SYN"
                    )

            # ACK only send ack to client no need to add seq num
            elif self.segment.get_flag() == SYN_ACK_FLAG:
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Received SYN-ACK"
                )
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending ACK")
                header = self.segment.get_header()
                header["seq"] = 1
                header["ack"] = 1
                self.segment.set_header(header)
                self.segment.set_flag(["ACK"])
                self.conn.send_data(self.segment.get_bytes(), client_addr)
                break
        print(
            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Handshake established")

    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]

        elif "\\" in self.pathfile:
            return self.pathfile.split("\\")[-1]

        return self.pathfile

    def get_extension_part(self):
        return self.filename.split(".")[-1]

    def get_name_part(self):
        return self.filename.split(".")[0]

    def open_file(self):
        try:
            file = open(f"{self.pathfile}", "rb")
            return file
        except FileNotFoundError:
            print(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)

    def get_filesize(self):
        try:
            filesize = os.path.getsize(self.pathfile)
            return filesize
        except FileNotFoundError:
            print(f"[!] {self.pathfile} doesn't exists. Exiting...")
            exit(1)

    def get_filechunk(self, index):
        offset = index * PAYLOAD_SIZE
        self.file.seek(offset)
        return self.file.read(PAYLOAD_SIZE)

    def choice_valid(self, choice: str):
        if choice.lower() == "y":
            return "y"
        elif choice.lower() == "n":
            return "n"
        else:
            return False

    def prompt_parallelization(self):
        choice = input(
            "[?] Do you want to enable paralelization for the server? (y/n)"
        ).lower()
        while not self.choice_valid(choice):
            print("[!] Please input correct input")
            choice = input(
                "[?] Do you want to enable paralelization for the server? (y/n)"
            ).lower()

        if choice == "y":
            self.is_parallel = True

    def shutdown(self):
        self.file.close()
        self.conn.close_socket()


if __name__ == "__main__":
    main = Server()
    main.prompt_parallelization()
    main.listen_for_clients()
    if not main.is_parallel:
        main.start_file_transfer()
