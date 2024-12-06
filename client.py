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
        message = input("1. What is the average moisture inside my kitchen fridge in the past three hours?\n"
                        "2. What is the average water consumption per cycle in my smart dishwasher?\n"
                        "3. Which device consumed more electricity among my three IoT devices (two refrigerators and a dishwasher)?\n")
        if int(message) not in range(1, 4):
            print("Sorry, this query cannot be processed. Please try one of the following: \n")
        
        else:
            print(f"Sending: {message}")
            socket.sendall(message.encode('utf-8'))

            if message.upper() == "STOP":
                print(f"Server stopped.")
                break

            # Receive message from server
            data = socket.recv(1024)
            print(f"Received: {data.decode('utf-8')}")

if __name__ == '__main__':
    main()  