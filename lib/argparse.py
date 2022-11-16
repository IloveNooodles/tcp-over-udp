import argparse


class Parser:
    def __init__(self, is_server: bool = False):
        self.broadcast_port = ""
        self.client_port = ""
        self.pathfile_input = ""
        self.pathfile_output = ""
        self.is_server = is_server
        if is_server:
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
            self.broadcast_port = getattr(args, "broadcast_port")
            self.pathfile_input = getattr(args, "pathfile_input")
        else:
            parser = argparse.ArgumentParser(
                description="Client for handling file transfer connection from server"
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
            self.client_port = getattr(args, "client_port")
            self.broadcast_port = getattr(args, "broadcast_port")
            self.pathfile_output = getattr(args, "pathfile_output")

    def get_values(self):
        if self.is_server:
            return self.broadcast_port, self.pathfile_input

        return self.client_port, self.broadcast_port, self.pathfile_output

    def __str__(self):
        if self.is_server:
            return f"Server Parser:\n Broadcast port: {self.broadcast_port}\n Input pathfile: {self.pathfile_input}"

        return f"Client Parser:\n Client Port: {self.client_port}\n Broadcast port: {self.broadcast_port}\n Output pathfile: {self.pathfile_input}"
