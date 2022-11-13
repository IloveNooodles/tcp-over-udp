import threading
from math import ceil
from socket import timeout as socket_timeout
from typing import Tuple

from lib.argparse import Parser
from lib.connection import Connection
from lib.constant import (
    ACK_FLAG,
    FIN_ACK_FLAG,
    PAYLOAD_SIZE,
    SEGMENT_SIZE,
    SYN_ACK_FLAG,
    SYN_FLAG,
    TIMEOUT_LISTEN,
    WINDOW_SIZE,
)
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
        self.is_parallel = False
        self.running_thread = None
        print(f"[!] Source file | {self.filename} | {self.filesize} bytes")

    def count_segment(self):
        return ceil(self.filesize / PAYLOAD_SIZE)

    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients.")
        while True:
            try:
                client = self.conn.listen_single_segment(TIMEOUT_LISTEN)
                client_address = client[1]
                ip, port = client_address
                # Create thread when parallel is on
                if self.is_parallel:
                    # check if the tuple is diff, if not then don't create thread
                    if self.running_thread == client_address:
                        continue

                    self.running_thread = client_address
                    send_file = threading.Thread(
                        target=self.start_file_transfer,
                        kwargs={"client_parallel": self.running_thread},
                    )
                    send_file.start()
                    continue
                else:
                    self.client_list.append(client_address)
                    print(f"[!] Recieved request from {ip}:{port}")
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

    def start_file_transfer(self, client_parallel=None):
        print(client_parallel)
        if not self.is_parallel:
            for client in self.client_list:
                self.three_way_handshake(client)
                self.send_metadata()
                self.file_transfer(client)
        else:
            self.three_way_handshake(client_parallel)
            self.send_metadata()
            self.file_transfer(client_parallel)

    def file_transfer(self, client_addr: Tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        list_segment = []
        num_of_segment = self.count_segment()
        # After three way handshake seq num is now 1
        # Flags is 0 for sending data
        seq = 1
        for i in range(num_of_segment):
            segment = Segment()
            data_to_set = self.data[i * PAYLOAD_SIZE : (i + 1) * PAYLOAD_SIZE]
            segment.set_payload(data_to_set)
            header = segment.get_header()
            header["seq"] = seq
            header["ack"] = 0
            segment.set_header(header)
            list_segment.append(segment)
            seq += 1

        window_size = min(num_of_segment, WINDOW_SIZE + 1)
        sequence_base = 0

        while sequence_base < num_of_segment:
            sequence_max = window_size
            for i in range(sequence_max):
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending Segment {sequence_base+i+1}"
                )
                if i + sequence_base < num_of_segment:
                    self.conn.send_data(
                        list_segment[i + sequence_base].get_bytes(), client_addr
                    )
            for i in range(sequence_max):
                try:
                    data, response_addr = self.conn.listen_single_segment()
                    segment = Segment()
                    segment.set_from_bytes(data)

                    # print("CURRENT SEGMENT: ", segment.get_header())
                    # print("CURRENT_sequence_base: ", sequence_base)
                    if (
                        client_addr[1] == response_addr[1]
                        and segment.get_flag() == ACK_FLAG
                        and segment.get_header()["ack"] == sequence_base + 1
                    ):
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved ACK {sequence_base+1}"
                        )
                        sequence_base += 1
                        window_size = min(num_of_segment - sequence_base, WINDOW_SIZE)
                    elif client_addr[1] != response_addr[1]:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved ACK from wrong client"
                        )
                    elif segment.get_flag() != ACK_FLAG:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved wrong flag"
                        )
                    else:
                        print(
                            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved Wrong ACK"
                        )
                        request_number = segment.get_header()["ack"]
                        sequence_max = (sequence_max - sequence_base) + request_number
                        sequence_base = request_number
                except socket_timeout:
                    print(
                        f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending prev seq num"
                    )
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
                data, response_addr = self.conn.listen_single_segment()
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

    def three_way_handshake(self, client_addr: Tuple[str, int]) -> bool:
        print(
            f"[!] [Client {client_addr[0]}:{client_addr[1]}] Initiating three way handshake..."
        )
        self.segment.set_flag(["SYN"])
        seq = 0
        while True:
            # SYN
            if self.segment.get_flag() == SYN_FLAG:
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending SYN")
                header = self.segment.get_header()
                header["seq"] = seq
                header["ack"] = 0
                self.conn.send_data(self.segment.get_bytes(), client_addr)
                try:
                    data, address = self.conn.listen_single_segment()
                    self.segment.set_from_bytes(data)
                    seq += 1

                except socket_timeout:
                    print(
                        f"[!] [Client {client_addr[0]}:{client_addr[1]}] [Timeout] ACK response timeout, resending SYN"
                    )
                    continue

            # ACK only send ack to client no need to add seq num
            elif self.segment.get_flag() == SYN_ACK_FLAG:
                print(
                    f"[!] [Client {client_addr[0]}:{client_addr[1]}] Recieved SYN-ACK"
                )
                print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Sending ACK")
                header = self.segment.get_header()
                header["ack"] = header["seq"]
                self.segment.set_header(header)
                self.segment.set_flag(["ACK"])
                self.conn.send_data(self.segment.get_bytes(), client_addr)
                break
        print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] Handshake established")

    def get_filename(self):
        if "/" in self.pathfile:
            return self.pathfile.split("/")[-1]

        elif "\\" in self.pathfile:
            return self.pathfile.split("\\")[-1]

        return self.pathfile

    def get_file_ext(self):
        return self.filename.split(".")[-1]

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

    def send_metadata(self):
        metadata_segment = Segment()
        metadata = b""
        filename = self.filename
        extension = self.get_file_ext()
        filesize = self.filesize
        metadata += filename.encode() + extension.encode() + str(filesize).encode()
        metadata_segment.set_payload(metadata)

    def shutdown(self):
        self.conn.close_socket()


if __name__ == "__main__":
    main = Server()
    main.prompt_parallelization()
    main.listen_for_clients()
    if not main.is_parallel:
        main.start_file_transfer()
    main.shutdown()
