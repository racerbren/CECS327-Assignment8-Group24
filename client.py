import signal
import socket
import argparse
import ipaddress
import sys


def main(
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address, port: int, buffer_size: int
):
    if ip.version == 4:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif ip.version == 6:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        raise ValueError("Invalid IP address.")
    commands: dict[str, str] = {}

    def get_commands():
        nonlocal commands
        s.sendall(b"COMMANDS")
        data = s.recv(buffer_size)
        if not data:
            raise ConnectionError("No data received.")
        data = data.decode("utf-8")
        commands = {}
        for line in data.split("\n"):
            line = line.strip()
            try:
                cmd, desc = line.split(":")
            except ValueError:
                continue
            commands[cmd.strip()] = desc.strip()
        if not "COMMANDS" in commands:
            commands["COMMANDS"] = "List available commands"
        if not "QUIT" in commands:
            commands["QUIT"] = "Exit the program"

    def print_commands():
        print("Available commands:")
        for key, value in commands.items():
            print(f"{key}: {value}")


    s.connect((str(ip), port))

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        s.close()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    print(f"Connected to server at {ip}:{port}")
    print("Enter 'QUIT' or press Ctrl+C to exit.")
    get_commands()

    print_commands()
    while True:
        message = ""
        while not message:
            message = input("> ")

        args = message.split()
        if len(args) > 1:
            cmd = args[0]
            args = args[1:]
        else:
            cmd = args[0]
            args = []
        cmd = cmd.strip().upper()
        args = [arg.strip() for arg in args]
        if cmd == "QUIT":
            print("Quitting.")
            break
        elif cmd == "COMMANDS":
            get_commands()
            print_commands()
            continue
        elif cmd in commands:
            s.sendall(f"{cmd} {" ".join(args)}".encode("utf-8"))
            data = s.recv(buffer_size)
            if not data:
                print("Connection closed.")
                break
            data = data.decode("utf-8")
            print(data)
        else:
            print("Invalid command. Please try again.")
            continue
    s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for IoT device queries.")
    parser.add_argument("--ip", type=str, default=None, help="IP address of the server")
    parser.add_argument(
        "--port", type=int, default=None, help="Port number of the server"
    )
    parser.add_argument(
        "--buffer_size", type=int, default=1024, help="Buffer size for receiving data"
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
    main(ip, port, args.buffer_size)
