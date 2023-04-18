# https://www.oreilly.com/library/view/python-cookbook/0596001673/ch10s03.html

import socket

# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Ensure that you can restart your server quickly when it terminates
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set the client socket's TCP "well-known port" number
sock.bind(('127.0.0.1', 8080))

# Set the number of clients waiting for connection that can be queued
sock.listen(5)

sock.settimeout(0.5)

# loop waiting for connections (terminate with Ctrl-C)
try:
    while 1:
        try:
            newSocket, address = sock.accept()
            print("Connected from", address)
            # loop serving the new client
            while 1:
                receivedData = newSocket.recv(1024)
                if not receivedData: break
                print("Received ", receivedData)
                # newSocket.send(b'TestMsg')
            newSocket.close()
            print("Disconnected from", address)
        except:
            pass
except KeyboardInterrupt:
    pass
finally:
    sock.close()