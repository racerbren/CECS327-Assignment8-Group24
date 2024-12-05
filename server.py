import socket
import os
import sys
import ipaddress
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://brenden:bNOqLuT6vD2l65rt@cecs327assignment7.mvzpl.mongodb.net/?retryWrites=true&w=majority&appName=CECS327Assignment7"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["test"]
meta = db["Table_metadata"]
col = db["Table_virtual"]

mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = input("Enter server IP address: ")
port = int(input("Enter server port number: "))

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

        elif data == "TBD":
            for item in col.find({'payload.asset_uid': "n43-l4s-165-p2l"}):
                print(item["payload"]["Ammeter"])

        #Send and encode message to client
        print(f"Server sending: {data}")
        incomingSocket.sendall(bytearray(str(data), encoding='utf-8'))

    incomingSocket.close()

if __name__ == '__main__':
    main()