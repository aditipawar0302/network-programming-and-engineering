
import sqlite3
import csv

DB_NAME = "network_monitor.db"


def export_table(table_name, output_file):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")

    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    connection.close()

    if not rows:
        print(f"No records found in {table_name}.")
        return

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Exported {len(rows)} records to {output_file}")


if __name__ == "__main__":
    export_table(
        "network_history",
        "network_history_report.csv"
    )

    export_table(
        "server_history",
        "server_history_report.csv"
    )

    print("\nDatabase reports generated successfully!")
