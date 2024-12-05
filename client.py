import socket
import os
import sys
import ipaddress

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():
    serverIP = input('Enter IP address to connect to: ')
    serverPort = input('Enter a port to connect to: ')
    socket.connect((serverIP, int(serverPort)))
    while True:
        # Send message to server
        message = input('Enter message to send to server: ')
        print(f"Sending: {message}")
        socket.sendall(message.encode('utf-8'))

        if message.upper() == "STOP":
            print(f"Server stopped.")
            break

        # Receive message from server
        data = socket.recv(1024)
        print(f"Recived: {data.decode('utf-8')}")

if __name__ == '__main__':
    main()