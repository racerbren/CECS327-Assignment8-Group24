import socket
import os
import sys
import ipaddress

mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = socket.gethostbyname(socket.gethostname())
port = 5555

mySocket.bind((server, port))
mySocket.listen(5)
print(f"Server listing for connections on {server}:{port}...")
incomingSocket, incomingAddress = mySocket.accept()

def main():
    while True:
        # Receive and decode message from client
        data = str(incomingSocket.recv(1024).decode('utf-8'))
        data = data.upper()    # Capitalize the message
        print(f"Server recieved: {data}")

        # End condition
        if data == "STOP":
            print(f"Serving ending...")
            break

        #Send and encode message to client
        print(f"Server sending: {data}")
        incomingSocket.sendall(bytearray(str(data), encoding='utf-8'))

    incomingSocket.close()

if __name__ == '__main__':
    main()