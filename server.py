import argparse
import os
import signal
import socket
import select
import sys
from typing import Callable
import ipaddress
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pymongo.mongo_client import MongoClient
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database

# uri = "mongodb+srv://brenden:bNOqLuT6vD2l65rt@cecs327assignment7.mvzpl.mongodb.net/?retryWrites=true&w=majority&appName=CECS327Assignment7"
# client = MongoClient(uri, server_api=ServerApi("1"))
# db = client["test"]
# meta = db["Table_metadata"]
# col = db["Table_virtual"]

# mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# server = input("Enter server IP address: ")
# port = int(input("Enter server port number: "))

# mySocket.bind((server, port))
# mySocket.listen(5)
# print(f"Server listing for connections on {server}:{port}...")
# incomingSocket, incomingAddress = mySocket.accept()


def main(
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
    port: int,
    buffer_size: int,
    db_client: MongoClient,
    db: Database,
    db_collection: Collection,
    db_meta: Collection,
):
    if ip.version == 4:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif ip.version == 6:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        raise ValueError("Invalid IP address.")

    # Define commands {command: (description, function, [(arg, desc)], return_desc)}
    commands: dict[
        str,
        tuple[
            Callable[[socket.socket, str, str, list[str]], None],
            str,
            list[tuple[str, str]],
            str,
        ],
    ]
    running = True
    clients: dict[socket.socket, str] = {}

    def cmd_commands(client: socket.socket, addr: str, cmd: str, args: list[str]):
        data = ""
        nonlocal commands
        for key, value in commands.items():
            data += f"{key}:{value[1]}\n"
        print(data)
        client.sendall(data.encode("utf-8"))

    def cmd_stop(client: socket.socket, addr: str, cmd: str, args: list[str]):
        nonlocal running
        running = False

    def cmd_help(client: socket.socket, addr: str, cmd: str, args: list[str]):
        nonlocal commands
        data = ""
        if not args:
            data += "Usage: HELP <command>\n"
            return
        c = args[0].upper()
        if c in commands.keys():
            data += f"{c}: {commands[c][1]}\n"
            for arg, desc in commands[c][2]:
                data += f"\t{arg}: {desc}\n"
            data += f"Returns: {commands[c][3]}\n"
        else:
            data += f"Command {c} not found.\n"
        client.sendall(data.encode("utf-8"))

    def cmd_moisture(client: socket.socket, addr: str, cmd: str, args: list[str]):
        total = 0
        i = 0
        for item in db_collection.find(
            {
                "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=3)},
                "payload.asset_uid": "n43-l4s-165-p2l",
            }
        ):
            total += Decimal(item["payload"]["Moisture Meter - Fridge Moisture Meter"])
            i += 1
        average = round((Decimal(total / i) / Decimal(40.0)) * 100, 2)
        client.sendall(f"{average}".encode("utf-8"))

    def cmd_gallons(client: socket.socket, addr: str, cmd: str, args: list[str]):
        total = 0
        i = 0
        for item in db_collection.find(
            {
                "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=2)},
                "payload.asset_uid": "nw4-asg-55o-ug3",
            }
        ):
            total += Decimal(item["payload"]["Water Consumption Sensor"])
            i += 1
        total = round(Decimal(total / Decimal(36.0)), 2)
        data = f"Average water consumption: {total} gallons per cycle\n"
        client.sendall(data.encode("utf-8"))

    def cmd_energy(client: socket.socket, addr: str, cmd: str, args: list[str]):
        fridge1 = 0
        dishwasher = 0
        fridge2 = 0

        # Fridge 1
        for item in db_collection.find(
            {
                "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
                "payload.asset_uid": "n43-l4s-165-p2l",
            }
        ):
            fridge1 += Decimal(item["payload"]["Ammeter"])
        # Dishwasher
        for item in db_collection.find(
            {
                "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
                "payload.asset_uid": "nw4-asg-55o-ug3",
            }
        ):
            dishwasher += Decimal(item["payload"]["Dishwasher Ammeter"])
        # Fridge 2
        for item in db_collection.find(
            {
                "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
                "payload.asset_uid": "4a9-8so-qj3-7a1",
            }
        ):
            fridge2 += Decimal(item["payload"]["Ammeter 2"])

        fridge1 /= Decimal(864.0)
        dishwasher /= Decimal(864.0)
        fridge2 /= Decimal(864.0)
        fridge1kwh = round((fridge1 * 120 * 24) / Decimal(10000.0), 2)
        dishwasherkwh = round((dishwasher * 120 * 24) / Decimal(10000.0), 2)
        fridge2kwh = round((fridge2 * 120 * 24) / Decimal(10000.0), 2)

        data = f"Fridge 1 energy consumption: {fridge1kwh}kWh\nDishwasher energy consumption: {dishwasherkwh}kWh\nFridge 2 energy consumption: {fridge2kwh}kWh\n"
        client.sendall(data.encode("utf-8"))

    commands = {
        "COMMANDS": (
            cmd_commands,
            "List available commands",
            [],
            "The list of commands, formatted as 'command:description'",
        ),
        "STOP": (cmd_stop, "Stop the server", [], "None"),
        "HELP": (
            cmd_help,
            "Get help for a command",
            [("command", "Command to get help for")],
            "Help for a command.",
        ),
        "MOISTURE": (
            cmd_moisture,
            "Get average moisture of kitchen fridge over past 3 hours",
            [],
            "Average moisture of kitchen fridge over past 3 hours.",
        ),
        "GALLONS": (
            cmd_gallons,
            "Get average gallons per dishwasher cycle (2 hours long cycle)",
            [],
            "Average gallons per dishwasher cycle (2 hours long cycle).",
        ),
        "ENERGY": (
            cmd_energy,
            "Get total energy consumption across 3 devices",
            [],
            "Total energy consumption across 3 devices.",
        ),
    }

    s.bind((str(ip), port))
    s.listen(5)
    s.setblocking(False)

    def signal_handler(sig, frame):
        print("You pressed Ctrl+C!")
        for sock in clients.keys():
            sock.close()
        s.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print(f"Server listening for connections on {ip}:{port}")

    while running:
        clients_list = list(clients.keys())
        readable, _, _ = select.select([s] + clients_list, [], [], 1)
        for sock in readable:
            if sock == s:
                client, addr = s.accept()
                clients[client] = addr
                print(f"Connected to {addr}")
                continue
            client = clients[sock]
            if not client:
                print(f"Unknown client {sock}")
                continue
            data = sock.recv(buffer_size)
            if not data:
                print(f"Client {client} disconnected.")
                del clients[sock]
                continue
            data = data.decode("utf-8")
            print(f"Received from {client}: {data}")
            cmd, *args = data.split()
            cmd = cmd.upper().strip()
            args = [arg.strip() for arg in args]
            print(f"Command: {cmd}, Args: {args}")

            if cmd in commands:
                commands[cmd][0](sock, client, cmd, args)
                continue
            else:
                sock.sendall(b"Invalid command. Please try again.")
                print(f"Invalid command {cmd} from {client}.")
                continue

    for sock in clients.keys():
        sock.close()
    s.close()

    #     # Receive and decode message from client
    #     data = str(incomingSocket.recv(1024).decode("utf-8"))
    #     data = data.upper()  # Capitalize the message
    #     print(f"Server recieved: {data}")

    #     # End condition
    #     if data == "STOP":
    #         print(f"Serving ending...")
    #         break

    #     # Average humidity of fridge over last 3 hours
    #     elif data == "1":
    #         total = 0
    #         i = 0
    #         for item in col.find(
    #             {
    #                 "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=3)},
    #                 "payload.asset_uid": "n43-l4s-165-p2l",
    #             }
    #         ):
    #             total += Decimal(
    #                 item["payload"]["Moisture Meter - Fridge Moisture Meter"]
    #             )
    #             i += 1
    #         average = round((Decimal(total / i) / Decimal(40.0)) * 100, 2)
    #         data = f"Average moisture of kitchen fridge over past 3 hours: {average}%\n"

    #     # Average gallons per dishwasher cycle  (2 hours long cycle)
    #     elif data == "2":
    #         total = 0
    #         i = 0
    #         for item in col.find(
    #             {
    #                 "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=2)},
    #                 "payload.asset_uid": "nw4-asg-55o-ug3",
    #             }
    #         ):
    #             total += Decimal(item["payload"]["Water Consumption Sensor"])
    #             i += 1
    #         total = round(Decimal(total / Decimal(36.0)), 2)
    #         data = f"Average water consumption: {total} gallons per cycle\n"

    #     # Total energy consumption across 3 devices
    #     elif data == "3":
    #         fridge1 = 0
    #         dishwasher = 0
    #         fridge2 = 0

    #         # Fridge 1
    #         for item in col.find(
    #             {
    #                 "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
    #                 "payload.asset_uid": "n43-l4s-165-p2l",
    #             }
    #         ):
    #             fridge1 += Decimal(item["payload"]["Ammeter"])
    #         # Dishwasher
    #         for item in col.find(
    #             {
    #                 "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
    #                 "payload.asset_uid": "nw4-asg-55o-ug3",
    #             }
    #         ):
    #             dishwasher += Decimal(item["payload"]["Dishwasher Ammeter"])
    #         # Fridge 2
    #         for item in col.find(
    #             {
    #                 "time": {"$gt": datetime.now(timezone.utc) - timedelta(hours=24)},
    #                 "payload.asset_uid": "4a9-8so-qj3-7a1",
    #             }
    #         ):
    #             fridge2 += Decimal(item["payload"]["Ammeter 2"])

    #         fridge1 /= Decimal(864.0)
    #         dishwasher /= Decimal(864.0)
    #         fridge2 /= Decimal(864.0)
    #         fridge1kwh = round((fridge1 * 120 * 24) / Decimal(10000.0), 2)
    #         dishwasherkwh = round((dishwasher * 120 * 24) / Decimal(10000.0), 2)
    #         fridge2kwh = round((fridge2 * 120 * 24) / Decimal(10000.0), 2)

    #         data = f"Fridge 1 energy consumption: {fridge1kwh}kWh\nDishwasher energy consumption: {dishwasherkwh}kWh\nFridge 2 energy consumption: {fridge2kwh}kWh\n"

    #     # Send and encode message to client
    #     print(f"Server sending: {data}")
    #     incomingSocket.sendall(bytearray(str(data), encoding="utf-8"))

    # incomingSocket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for IoT device queries.")
    parser.add_argument("--ip", type=str, default=None, help="IP address of the server")
    parser.add_argument(
        "--port", type=int, default=None, help="Port number of the server"
    )
    parser.add_argument(
        "--buffer_size", type=int, default=1024, help="Buffer size for receiving data"
    )
    parser.add_argument(
        "--db-uri", type=str, default=None, help="URI for MongoDB connection"
    )
    parser.add_argument(
        "--db-name", type=str, default=None, help="Name of the database to use"
    )
    parser.add_argument(
        "--db-collection",
        type=str,
        default="Table_virtual",
        help="Name of the collection to use",
    )
    parser.add_argument(
        "--db-meta",
        type=str,
        default="Table_virtual",
        help="Name of the metadata collection to use",
    )
    args = parser.parse_args()

    ip = None
    while ip is None:
        DEFAULT_IP = "127.0.0.1"
        if args.ip is None:
            args.ip = input(f"Enter IP address to connect to [{DEFAULT_IP}]: ")
            if args.ip == "":
                args.ip = DEFAULT_IP
        ip = ipaddress.ip_address(args.ip)
        if not ip or ip.is_unspecified:
            print("Invalid IP address.")
            args.ip = None
            ip = None

    port = None
    while port is None:
        DEFAULT_PORT = 8080
        if args.port is None:
            args.port = input(f"Enter port number to connect to [{DEFAULT_PORT}]: ")
            if args.port == "":
                args.port = DEFAULT_PORT
        try:
            port = int(args.port)
            if port < 0 or port > 65535:
                raise ValueError
        except ValueError:
            print("Invalid port number.")
            args.port = None
            port = None

    db_client = None
    while db_client is None:
        if args.db_uri is None:
            args.db_uri = os.getenv("MONGO_URI")
            if args.db_uri is None:
                args.db_uri = input(f"Enter MongoDB URI to connect to: ")
        try:
            db_client = MongoClient(args.db_uri)
        except:
            print("Invalid MongoDB URI.")
            args.db_uri = None
            db_client = None

    db = None
    while db is None:
        if args.db_name is None:
            args.db_name = input(f"Enter database name to use: ")
        db = db_client[args.db_name]
        if db is None:
            print("Invalid database name.")
            args.db_name = None
            db = None

    db_collection = None
    while db_collection is None:
        if args.db_collection is None:
            args.db_collection = input(f"Enter collection name to use: ")
        db_collection = db[args.db_collection]
        if db_collection is None:
            print("Invalid collection name.")
            args.db_collection = None
            db_collection = None

    db_meta = None
    while db_meta is None:
        if args.db_meta is None:
            args.db_meta = input(f"Enter metadata collection name to use: ")
        db_meta = db[args.db_meta]
        if db_meta is None:
            print("Invalid metadata collection name.")
            args.db_meta = None
            db_meta = None

    main(ip, port, args.buffer_size, db_client, db, db_collection, db_meta)
