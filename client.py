
from lib.argparse import Parser
from lib.connection import Connection
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

    def connect(self):
        self.conn.send_data(b"REQ", (self.conn.ip, self.broadcast_port))
  
    def three_way_handshake(self):
        while True:
            
            data, address = self.conn.listen_single_segment()
            self.segment.set_from_bytes(data)
            break

    def listen_file_transfer(self):
        try:
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
