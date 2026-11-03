
import sqlite3

DB_NAME = "network_monitor.db"


def view_network_history():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT timestamp, upload_speed, download_speed,
               total_bytes_sent, total_bytes_received
        FROM network_history
        ORDER BY id DESC
        LIMIT 10
    """)

    records = cursor.fetchall()

    print("\n===== NETWORK MONITORING HISTORY =====")

    if not records:
        print("No network records found.")

    for record in records:
        print(
            f"Time: {record[0]} | "
            f"Upload: {record[1]:.2f} B/s | "
            f"Download: {record[2]:.2f} B/s | "
            f"Sent: {record[3]} bytes | "
            f"Received: {record[4]} bytes"
        )

    connection.close()


def view_server_history():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT timestamp, server_name, host, port,
               status, response_time, availability
        FROM server_history
        ORDER BY id DESC
        LIMIT 10
    """)

    records = cursor.fetchall()

    print("\n===== SERVER MONITORING HISTORY =====")

    if not records:
        print("No server records found.")

    for record in records:
        print(
            f"Time: {record[0]} | "
            f"Server: {record[1]} | "
            f"Host: {record[2]}:{record[3]} | "
            f"Status: {record[4]} | "
            f"Response: {record[5]} ms | "
            f"Availability: {record[6]}%"
        )

    connection.close()


if __name__ == "__main__":
    view_network_history()
    view_server_history()
