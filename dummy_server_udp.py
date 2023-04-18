# https://pythontic.com/modules/socket/udp-client-server-example

import socket

localIP     = "127.0.0.1"
localPort   = 8080
bufferSize  = 1024

sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
sock.bind((localIP, localPort))
sock.settimeout(0.5)

print("UDP server up and listening")
 
try:
    while(True):
        try:
            bytesAddressPair = sock.recvfrom(bufferSize)
            message = bytesAddressPair[0]
            address = bytesAddressPair[1]

            print(f"Received {message} from {address}")

            sock.sendto(b'TestMsg', address)
        except:
            pass
except KeyboardInterrupt:
    pass