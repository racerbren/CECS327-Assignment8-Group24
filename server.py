import socket
import os
import sys
import ipaddress
import pymongo
from decimal import Decimal
from datetime import datetime, timedelta, timezone
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
        
        #Average humidity of fridge over last 3 hours
        elif data == "1":
            total = 0
            i = 0
            for item in col.find({'time': {"$gt": datetime.now(timezone.utc) - timedelta(hours=3)},
                                  'payload.asset_uid': "n43-l4s-165-p2l"}):
                total += Decimal(item["payload"]["Moisture Meter - Fridge Moisture Meter"])
                i += 1
            average = round((Decimal(total / i) / Decimal(40.0)) * 100, 2)
            data = f"Average moisture of kitchen fridge over past 3 hours: {average}%\n"

        #Average gallons per dishwasher cycle  (2 hours long cycle)
        elif data == "2":
            total = 0
            i = 0
            for item in col.find({'time': {"$gt": datetime.now(timezone.utc) - timedelta(hours=2)},
                                  'payload.asset_uid': "nw4-asg-55o-ug3"}):
                total += Decimal(item["payload"]["Water Consumption Sensor"])
                i += 1
            total = round(Decimal(total / Decimal(36.0)), 2)
            data = f"Average water consumption: {total} gallons per cycle\n"

        #Total energy consumption across 3 devices
        elif data == "3":
            fridge1 = 0
            dishwasher = 0
            fridge2 = 0

            #Fridge 1
            for item in col.find({'time': {"$gt": datetime.now(timezone.utc) - timedelta(hours=3)},
                                  'payload.asset_uid': "n43-l4s-165-p2l"}):
                fridge1 += Decimal(item["payload"]["Ammeter"])
            #Dishwasher
            for item in col.find({'time': {"$gt": datetime.now(timezone.utc) - timedelta(hours=1)},
                                  'payload.asset_uid': "nw4-asg-55o-ug3"}):
                dishwasher += Decimal(item["payload"]["Ammeter"])
            #Fridge 2
            for item in col.find({'time': {"$gt": datetime.now(timezone.utc) - timedelta(hours=1)},
                                  'payload.asset_uid': "4a9-8so-qj3-7a1"}):
                fridge2 += Decimal(item["payload"]["Ammeter"])

        #Send and encode message to client
        print(f"Server sending: {data}")
        incomingSocket.sendall(bytearray(str(data), encoding='utf-8'))

    incomingSocket.close()

if __name__ == '__main__':
    main()