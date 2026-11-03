import socket

target = "127.0.0.1"

for port in [135, 445, 80, 443]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            result = sock.connect_ex((target, port))

            if result == 0:
                print(f"[OPEN] Port {port}")
            else:
                print(f"[NOT OPEN] Port {port} | Error code: {result}")

    except socket.error as error:
        print(f"[ERROR] Port {port}: {error}")