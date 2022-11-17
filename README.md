# Kit IF3130 - Jaringan Komputer 2022

Repository template tugas besar 2 - IF3130 - Jaringan Komputer - 2022

# TCP Over UDP

This repository contains how to simulate TCP connection over UDP socket. It consist of simple server and client, server can send file to a or multiple client. There are no non builtin library are used for this implementation.

## Members - masuktipi

| Name                           |   NIM    |
| ------------------------------ | :------: |
| Muhammad Garebaldhie ER Rahman | 13520029 |
| Rayhan Kinan Muhannad          | 13520065 |
| Aira Thalca Avila Putra        | 13520101 |

## Usage

server.py

```
usage: server.py [-h] [broadcast port] [Path file input]

Server for handling file transfer connection to client

positional arguments:
  [broadcast port]   broadcast port used for all client
  [Path file input]  path to file you want to send

options:
  -h, --help         show this help message and exit
```

client.py

```
usage: client.py [-h] [client port] [broadcast port] [path file output]

Client for handling file transfer connection from server

positional arguments:
  [client port]       client port to start the service
  [broadcast port]    broadcast port used for destination address
  [path file output]  output path location

options:
  -h, --help          show this help message and exit
```

## Features implemented

1. Three way handshake
2. Go Back N when network are unreliable
3. Paralelization (server can transfer file to each client paralel)
4. Optimize file read
5. Metadata
6. File will be write in `out` directory

## How to use

1. Run server by inserting the broadcast port and source file instructions in [Usage](#usage)
   `python server.py 5000 ./test/tu.txt`
2. If filename aren't exists program will exit
3. Server will ask if client want to use paralellization.
4. Run client by inserting the port, broadcast port and filename see in [Usage](#usage)
   `python client.py 5001 5000 a.txt`
5. File will be write in `out/a.txt`
6. Make sure the port are different for `broadcast addr` and `client addr`

## References

1. [Validate data with CRC](https://quickbirdstudios.com/blog/validate-data-with-crc/)
2. [Understanding CRC](http://www.sunshine2k.de/articles/coding/crc/understanding_crc.html)
3. [TCP Flags](https://www.keycdn.com/support/tcp-flags)
4. [Three way Handshake](https://www.guru99.com/tcp-3-way-handshake.html#:~:text=TCP%20Three%2DWay%20Handshake%20Process,-TCP%20traffic%20begins&text=It%20sends%20a%20segment%20with,should%20be%20its%20sequence%20number.)
