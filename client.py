
from lib.argparse import Parser
from lib.connection import Connection
from lib.constant import ACK_FLAG, SEGMENT_SIZE, SYN_ACK_FLAG, SYN_FLAG
from lib.segment import Segment


class Client:
    def __init__(self):
        args = Parser(is_server=False)
        client_port, broadcast_port, pathfile_output = args.get_values()
        self.client_port = client_port
        self.broadcast_port = broadcast_port
        self.pathfile_output = pathfile_output
        self.conn = Connection(broadcast_port=broadcast_port, port=client_port, is_server=False)
        self.segment = Segment()
        self.seq = 0
        self.ack = 0

    def connect(self):
        self.conn.send_data(self.segment.get_bytes(), (self.conn.ip, self.broadcast_port))
  
    def three_way_handshake(self):
        while True:
            # SYN-ACK
            data, server_addr = None, None
            try:
                data, server_addr = self.conn.listen_single_segment()
                self.segment.set_from_bytes(data)
                print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Recieve SYN")
            except:
                print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] [Timeout] SYN response timeout")

            print(self.segment)
            if self.segment.get_flag() == SYN_FLAG:
                self.segment.set_flag(["SYN", "ACK"])
                header = self.segment.get_header()
                header['ack'] = header['seq'] + 1
                header['seq'] = self.seq
                self.conn.send_data(self.segment.get_bytes(), server_addr)
                self.seq += 1
                print(f"[!] [Server {server_addr[0]}:{server_addr[1]}] Sending SYN-ACK")
                break


    def listen_file_transfer(self):
        try:
            for i in range(len(self.pathfile_output) - 1, -1, -1):
                if(self.pathfile_output[i] == '/'):
                    self.pathfile_output = self.pathfile_output[i+1:]
                    break
            file = open(f"out/{self.pathfile_output}", "wb")
            file.write(self.segment.get_payload())
            file.close()
        except:
            print(f"[!] {self.pathfile_output} doesn't exists. Exiting...")
            exit(1)

if __name__ == "__main__":
    main = Client()
    main.connect()
    main.three_way_handshake()
    main.listen_file_transfer()
