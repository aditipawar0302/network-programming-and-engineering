import socket
import threading

HOST = "127.0.0.1"
PORT = 5000


def receive_messages(client):
    while True:
        try:
            message = client.recv(1024)

            if not message:
                print("\nDisconnected from server.")
                break

            print("\n" + message.decode())

        except OSError:
            print("\nConnection closed.")
            break


def main():
    nickname = input("Enter your nickname: ").strip()

    if not nickname:
        print("Nickname cannot be empty.")
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))

        response = client.recv(1024)

        if response == b"NICK":
            client.sendall(nickname.encode())

        print("Connected to the chat server!")
        print("Type /quit to leave the chat.\n")

        receive_thread = threading.Thread(
            target=receive_messages,
            args=(client,),
            daemon=True
        )

        receive_thread.start()

        while receive_thread.is_alive():
            try:
                message = input()

                if message.strip() == "/quit":
                    client.sendall(b"/quit")
                    break

                if message.strip():
                    client.sendall(message.encode())

            except (EOFError, KeyboardInterrupt):
                break

    except ConnectionRefusedError:
        print("Unable to connect. Is the server running?")

    except OSError as error:
        print(f"Network error: {error}")

    finally:
        client.close()
        print("Chat client closed.")


if __name__ == "__main__":
    main()
