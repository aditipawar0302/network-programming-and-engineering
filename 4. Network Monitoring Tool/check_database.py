import sqlite3

connection = sqlite3.connect("network_monitor.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM network_history")
print("Network records:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM server_history")
print("Server records:", cursor.fetchone()[0])

connection.close()