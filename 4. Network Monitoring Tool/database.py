
import sqlite3
from datetime import datetime

DB_NAME = "network_monitor.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            upload_speed REAL,
            download_speed REAL,
            total_bytes_sent INTEGER,
            total_bytes_received INTEGER,
            packets_sent INTEGER,
            packets_received INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            server_name TEXT,
            host TEXT,
            port INTEGER,
            status TEXT,
            response_time REAL,
            availability REAL,
            total_checks INTEGER,
            failed_checks INTEGER
        )
    """)

    connection.commit()
    connection.close()


def save_network_data(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO network_history (
            timestamp,
            upload_speed,
            download_speed,
            total_bytes_sent,
            total_bytes_received,
            packets_sent,
            packets_received
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["upload_speed_bytes_per_second"],
        data["download_speed_bytes_per_second"],
        data["total_bytes_sent"],
        data["total_bytes_received"],
        data["packets_sent"],
        data["packets_received"]
    ))

    connection.commit()
    connection.close()


def save_server_data(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO server_history (
            timestamp,
            server_name,
            host,
            port,
            status,
            response_time,
            availability,
            total_checks,
            failed_checks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["server"],
        data["host"],
        data["port"],
        data["status"],
        data["response_time_ms"],
        data["availability_percent"],
        data["total_checks"],
        data["failed_checks"]
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("SQLite database initialized successfully!")
