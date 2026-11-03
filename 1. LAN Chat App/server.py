import socket
import threading
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000

clients = {}
clients_lock = threading.Lock()


def broadcast(message, sender=None):
    disconnected = []

    with clients_lock:
        for client in list(clients.keys()):
            if client != sender:
                try:
                    client.sendall(message)
                except OSError:
                    disconnected.append(client)

        for client in disconnected:
            remove_client(client)


def remove_client(client):
    with clients_lock:
        nickname = clients.pop(client, None)

    if nickname:
        try:
            client.close()
        except OSError:
            pass

        print(f"{nickname} disconnected.")

        timestamp = datetime.now().strftime("%H:%M:%S")
        broadcast(
            f"[{timestamp}] {nickname} left the chat!".encode(),
            client
        )


def handle_client(client):
    try:
        client.sendall(b"NICK")
        nickname = client.recv(1024).decode().strip()

        if not nickname:
            return

        with clients_lock:
            clients[client] = nickname

        print(f"{nickname} joined the chat.")

        timestamp = datetime.now().strftime("%H:%M:%S")
        broadcast(
            f"[{timestamp}] {nickname} joined the chat!".encode(),
            client
        )

        client.sendall(b"Connected to the server!")

        while True:
            message = client.recv(1024)

            if not message:
                break

            text = message.decode().strip()

            if text == "/quit":
                break

            if text:
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = (
                    f"[{timestamp}] {nickname}: {text}"
                )

                print(formatted_message)
                broadcast(formatted_message.encode(), client)

    except (ConnectionResetError, OSError):
        print("Client connection lost.")

    finally:
        remove_client(client)


def receive_connections():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen()

    print(f"Chat server running on {HOST}:{PORT}")
    print("Waiting for connections...")

    try:
        while True:
            client, address = server.accept()

            print(f"New connection: {address}")

            thread = threading.Thread(
                target=handle_client,
                args=(client,),
                daemon=True
            )
            thread.start()

    except KeyboardInterrupt:
        print("\nServer shutting down.")

    finally:
        with clients_lock:
            connected_clients = list(clients.keys())

        for client in connected_clients:
            try:
                client.close()
            except OSError:
                pass

        server.close()


if __name__ == "__main__":
    receive_connections()