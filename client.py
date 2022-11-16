from socket import timeout as socket_timeout

from lib.argparse import Parser
from lib.connection import Connection
from lib.constant import (ACK_FLAG, FIN_FLAG, SYN_ACK_FLAG, SYN_FLAG,
                          TIMEOUT_LISTEN)
from lib.segment import Segment


class Client:
    def __init__(self):
        args = Parser(is_server=False)
        client_port, broadcast_port, pathfile_output = args.get_values()
        self.client_port = client_port
        self.broadcast_port = broadcast_port
        self.pathfile_output = pathfile_output
        self.conn = Connection(
            broadcast_port=broadcast_port, port=client_port, is_server=False
        )
        self.segment = Segment()

    def connect(self):
        self.conn.send_data(
            self.segment.get_bytes(), (self.conn.ip, self.broadcast_port)
        )

    def three_way_handshake(self):
        end = False
        seq = 0
        while not end:
            # SYN-ACK
            data, server_addr = None, ("localhost", self.broadcast_port)
            try:
                data, server_addr = self.conn.listen_single_segment(TIMEOUT_LISTEN)
                self.segment.set_from_bytes(data)
                print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved SYN")
            except socket_timeout:
                print(
                    f"[!] [Server {server_addr[0]}:{server_addr[1]}] [Timeout] SYN response timeout"
                )
                continue

            if self.segment.get_flag() == SYN_FLAG:
                self.segment.set_flag(["SYN", "ACK"])
                header = self.segment.get_header()
                header["ack"] = header["seq"] + 1
                header["seq"] = seq
                seq += 1
                print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Sending SYN-ACK")
                self.conn.send_data(self.segment.get_bytes(), server_addr)
                ack = False
                while not ack:
                  try:
                      data, server_addr = self.conn.listen_single_segment(TIMEOUT_LISTEN)
                      ackFlag = Segment()
                      ackFlag.set_from_bytes(data)
                      if ackFlag.get_flag() == ACK_FLAG:
                          print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved ACK")
                          print(
                              f"[!] [Server {server_addr[0]}:{server_addr[1]}] Handshake established"
                          )
                          end = True
                          ack = True
                          break
                  except socket_timeout:
                      print(
                          f"[!] [Server {server_addr[0]}:{server_addr[1]}] [Timeout] ACK response timeout"
                      )
                      self.conn.send_data(self.segment.get_bytes(), server_addr)

    def sendACK(self, server_addr, ackNumber):
        response = Segment()
        response.set_flag(["ACK"])
        header = response.get_header()
        header["seq"] = 0
        header["ack"] = ackNumber
        response.set_header(header)
        self.conn.send_data(response.get_bytes(), server_addr)

    def listen_file_transfer(self):
        raw_data = b""
        request_number = 0
        data, server_addr = None, None
        while True:
            try:
                data, server_addr = self.conn.listen_single_segment()
                if server_addr[1] == self.broadcast_port:
                    self.segment.set_from_bytes(data)
                    # print("CURRENT ACK: ", self.segment.get_header())
                    # print("CURRENT_request_number: ", request_number)
                    if (
                        self.segment.valid_checksum()
                        and self.segment.get_header()["seq"] == request_number + 1
                    ):
                        payload = self.segment.get_payload()
                        raw_data += payload
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved Segment {request_number+1}"
                        )
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Sending ACK {request_number+1}"
                        )
                        self.sendACK(server_addr, request_number + 1)
                        request_number += 1
                        continue
                    elif self.segment.get_flag() == FIN_FLAG:
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved FIN"
                        )
                        break
                    elif self.segment.get_header()["seq"] < request_number + 1:
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved Segment {self.segment.get_header()['seq']} [Duplicate]"
                        )
                    elif self.segment.get_header()["seq"] > request_number + 1:
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved Segment {self.segment.get_header()['seq']} [Out-Of-Order]"
                        )
                    else:
                        print(
                            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved Segment {self.segment.get_header()['seq']} [Corrupt]"
                        )
                else:
                    print(
                        f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved Segment {self.segment.get_header()['seq']} [Wrong port]"
                    )
                self.sendACK(server_addr, request_number)
            except socket_timeout:
                print(
                    f"[!] [Server {server_addr[0]}:{server_addr[1]}] [Timeout] timeout error, resending prev seq num"
                )
                self.sendACK(server_addr, request_number)

        # sent FIN-ACK and wait for ACK to tearing down connection
        print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Sending FIN-ACK")
        # send FIN ACK
        finack = Segment()
        finack.set_header({"ack": request_number + 1, "seq": request_number + 1})
        finack.set_flag(["FIN", "ACK"])
        self.conn.send_data(finack.get_bytes(), server_addr)
        ack = False
        while not ack:
            try:
                data, server_addr = self.conn.listen_single_segment()
                ackSegment = Segment()
                ackSegment.set_from_bytes(data)
                if ackSegment.get_flag() == ACK_FLAG:
                    print(
                        f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieved ACK. Tearing down connection."
                    )
                    ack = True
            except socket_timeout:
                print(
                    f"[!] [Server {server_addr[0]}:{server_addr[1]}] [Timeout] timeout error, resending FIN ACK"
                )
                self.conn.send_data(finack.get_bytes(), server_addr)
        # Finish get ack from server try to write file
        print(
            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Data recieved successfuly"
        )
        print(
            f"[!] [Server {server_addr[0]}:{server_addr[1]}] Writing file to out/{self.pathfile_output}"
        )
        try:
            for i in range(len(self.pathfile_output) - 1, -1, -1):
                if self.pathfile_output[i] == "/":
                    self.pathfile_output = self.pathfile_output[i + 1 :]
                    break
            file = open(f"out/{self.pathfile_output}", "wb")
            file.write(raw_data)
            file.close()
            print(
                f"[!] [Server {server_addr[0]}:{server_addr[1]}] File transfer complete"
            )
        except FileNotFoundError:
            print(f"[!] {self.pathfile_output} doesn't exists. Exiting...")
            exit(1)

    def recieve_metadata(self):
          pass
    
    def shutdown(self):
        self.conn.close_socket()


if __name__ == "__main__":
    main = Client()
    main.connect()
    main.three_way_handshake()
    main.recieve_metadata()
    main.listen_file_transfer()
    main.shutdown()
