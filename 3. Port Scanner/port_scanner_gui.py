import socket
import csv
import threading
import queue
import tkinter as tk

from tkinter import ttk, messagebox, filedialog
from concurrent.futures import ThreadPoolExecutor


# ---------------- CONFIGURATION ----------------

MAX_WORKERS = 50
SOCKET_TIMEOUT = 2

COMMON_PORTS = {
    20: "FTP Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    135: "MS RPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP Proxy",
    8443: "HTTPS Alternative"
}


# ---------------- PORT SCANNER ----------------

def get_service_name(port):
    """Return the common service name for a port."""

    if port in COMMON_PORTS:
        return COMMON_PORTS[port]

    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "Unknown"


def scan_port(target, port):
    """
    Scan one TCP port.

    Uses blocking connect() with a timeout.
    """

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            sock.settimeout(SOCKET_TIMEOUT)

            try:
                sock.connect((target, port))

                service = get_service_name(port)

                # Try to retrieve a service banner.
                try:
                    sock.settimeout(0.5)
                    banner = sock.recv(1024).decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not banner:
                        banner = "No banner received"

                except socket.timeout:
                    banner = "No banner received"

                except OSError:
                    banner = "Banner unavailable"

                return {
                    "port": port,
                    "status": "OPEN",
                    "service": service,
                    "banner": banner
                }

            except ConnectionRefusedError:
                return {
                    "port": port,
                    "status": "CLOSED",
                    "service": "-",
                    "banner": "-"
                }

            except socket.timeout:
                return {
                    "port": port,
                    "status": "FILTERED/TIMEOUT",
                    "service": "-",
                    "banner": "-"
                }

            except OSError as error:

                win_error = getattr(error, "winerror", None)

                # Windows connection refused.
                if win_error == 10061:
                    status = "CLOSED"

                # Windows connection timed out.
                elif win_error == 10060:
                    status = "FILTERED/TIMEOUT"

                else:
                    status = "ERROR"

                return {
                    "port": port,
                    "status": status,
                    "service": "-",
                    "banner": str(error)
                }

    except OSError as error:
        return {
            "port": port,
            "status": "ERROR",
            "service": "-",
            "banner": str(error)
        }


# ---------------- GUI APPLICATION ----------------

class PortScannerGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Python Network Port Scanner")
        self.root.geometry("1050x750")
        self.root.minsize(850, 600)

        self.results = []
        self.result_queue = queue.Queue()
        self.executor = None
        self.futures = []
        self.completed_count = 0
        self.total_ports = 0
        self.scanning = False

        self.create_widgets()

    # ---------------- CREATE GUI ----------------

    def create_widgets(self):

        title = tk.Label(
            self.root,
            text="NETWORK PORT SCANNER",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        # Target IP
        tk.Label(
            input_frame,
            text="Target IP / Host:"
        ).grid(row=0, column=0, padx=5, pady=5)

        self.target_entry = tk.Entry(
            input_frame,
            width=25
        )
        self.target_entry.grid(row=0, column=1, padx=5)

        self.target_entry.insert(0, "127.0.0.1")

        # Start port
        tk.Label(
            input_frame,
            text="Start Port:"
        ).grid(row=0, column=2, padx=5)

        self.start_port_entry = tk.Entry(
            input_frame,
            width=10
        )
        self.start_port_entry.grid(row=0, column=3, padx=5)

        self.start_port_entry.insert(0, "1")

        # End port
        tk.Label(
            input_frame,
            text="End Port:"
        ).grid(row=0, column=4, padx=5)

        self.end_port_entry = tk.Entry(
            input_frame,
            width=10
        )
        self.end_port_entry.grid(row=0, column=5, padx=5)

        self.end_port_entry.insert(0, "100")

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.scan_button = tk.Button(
            button_frame,
            text="Start Scan",
            width=15,
            command=self.start_scan
        )
        self.scan_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop Scan",
            width=15,
            command=self.stop_scan,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.export_button = tk.Button(
            button_frame,
            text="Export CSV",
            width=15,
            command=self.export_csv
        )
        self.export_button.grid(row=0, column=2, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=700,
            mode="determinate"
        )
        self.progress.pack(pady=10, fill="x", padx=30)

        self.progress_label = tk.Label(
            self.root,
            text="Ready to scan"
        )
        self.progress_label.pack()

        # Statistics
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(pady=10)

        self.total_label = tk.Label(
            stats_frame,
            text="Total: 0",
            font=("Arial", 11, "bold")
        )
        self.total_label.grid(row=0, column=0, padx=15)

        self.open_label = tk.Label(
            stats_frame,
            text="Open: 0",
            fg="green",
            font=("Arial", 11, "bold")
        )
        self.open_label.grid(row=0, column=1, padx=15)

        self.closed_label = tk.Label(
            stats_frame,
            text="Closed: 0",
            fg="red",
            font=("Arial", 11, "bold")
        )
        self.closed_label.grid(row=0, column=2, padx=15)

        self.filtered_label = tk.Label(
            stats_frame,
            text="Filtered/Timeout: 0",
            fg="orange",
            font=("Arial", 11, "bold")
        )
        self.filtered_label.grid(row=0, column=3, padx=15)

        # Results table
        table_frame = tk.Frame(self.root)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        columns = (
            "Port",
            "Status",
            "Service",
            "Banner"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading("Port", text="Port")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Service", text="Service")
        self.tree.heading("Banner", text="Banner")

        self.tree.column("Port", width=80, anchor="center")
        self.tree.column("Status", width=150, anchor="center")
        self.tree.column("Service", width=180, anchor="center")
        self.tree.column("Banner", width=450)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Status: Idle",
            anchor="w"
        )
        self.status_label.pack(
            fill="x",
            padx=20,
            pady=5
        )

    # ---------------- START SCAN ----------------

    def start_scan(self):

        if self.scanning:
            return

        target = self.target_entry.get().strip()

        try:
            start_port = int(self.start_port_entry.get())
            end_port = int(self.end_port_entry.get())

            if not target:
                raise ValueError("Enter a target IP or hostname.")

            if not (1 <= start_port <= 65535):
                raise ValueError("Start port must be between 1 and 65535.")

            if not (1 <= end_port <= 65535):
                raise ValueError("End port must be between 1 and 65535.")

            if start_port > end_port:
                raise ValueError("Start port cannot exceed end port.")

            # Validate and resolve the target.
            target = socket.gethostbyname(target)

        except ValueError as error:
            messagebox.showerror("Invalid Input", str(error))
            return

        except socket.gaierror:
            messagebox.showerror(
                "Invalid Target",
                "Could not resolve the target hostname or IP address."
            )
            return

        # Reset previous results.
        self.results.clear()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.result_queue = queue.Queue()

        self.completed_count = 0

        ports = range(start_port, end_port + 1)

        self.total_ports = len(ports)

        self.progress["maximum"] = self.total_ports
        self.progress["value"] = 0

        self.update_statistics()

        self.scanning = True

        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.progress_label.config(text="Scanning...")
        self.status_label.config(
            text=f"Scanning {target} | Ports {start_port}-{end_port}"
        )

        # Start background scanning.
        self.executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        )

        self.futures = []

        for port in ports:
            future = self.executor.submit(
                scan_port,
                target,
                port
            )

            self.futures.append(future)

        # Begin checking scan results on the Tkinter main thread.
        self.root.after(100, self.check_scan_results)

    # ---------------- CHECK RESULTS ----------------

    def check_scan_results(self):

        if not self.scanning:
            return

        for future in self.futures:

            if future.done() and not getattr(
                future, "_processed", False
            ):

                future._processed = True

                try:
                    result = future.result()
                    self.result_queue.put(result)

                except Exception as error:
                    self.result_queue.put({
                        "port": "-",
                        "status": "ERROR",
                        "service": "-",
                        "banner": str(error)
                    })

        # Process results on the GUI thread.
        while not self.result_queue.empty():

            result = self.result_queue.get()

            self.results.append(result)

            self.completed_count += 1

            self.tree.insert(
                "",
                tk.END,
                values=(
                    result["port"],
                    result["status"],
                    result["service"],
                    result["banner"]
                )
            )

        self.progress["value"] = self.completed_count

        self.progress_label.config(
            text=f"Scanned {self.completed_count} / {self.total_ports} ports"
        )

        self.update_statistics()

        if self.completed_count >= self.total_ports:

            self.scanning = False

            if self.executor:
                self.executor.shutdown(
                    wait=False,
                    cancel_futures=False
                )

            self.scan_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

            self.progress_label.config(
                text="Scan completed successfully"
            )

            self.status_label.config(
                text="Status: Scan completed"
            )

            return

        self.root.after(100, self.check_scan_results)

    # ---------------- UPDATE STATISTICS ----------------

    def update_statistics(self):

        open_count = sum(
            1 for result in self.results
            if result["status"] == "OPEN"
        )

        closed_count = sum(
            1 for result in self.results
            if result["status"] == "CLOSED"
        )

        filtered_count = sum(
            1 for result in self.results
            if result["status"] == "FILTERED/TIMEOUT"
        )

        self.total_label.config(
            text=f"Total: {self.completed_count}"
        )

        self.open_label.config(
            text=f"Open: {open_count}"
        )

        self.closed_label.config(
            text=f"Closed: {closed_count}"
        )

        self.filtered_label.config(
            text=f"Filtered/Timeout: {filtered_count}"
        )

    # ---------------- STOP SCAN ----------------

    def stop_scan(self):

        if not self.scanning:
            return

        self.scanning = False

        if self.executor:
            self.executor.shutdown(
                wait=False,
                cancel_futures=True
            )

        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        self.progress_label.config(
            text="Scan stopped"
        )

        self.status_label.config(
            text="Status: Scan stopped by user"
        )

    # ---------------- EXPORT CSV ----------------

    def export_csv(self):

        if not self.results:
            messagebox.showwarning(
                "No Results",
                "There are no scan results to export."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="port_scan_results.csv"
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as csvfile:

                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=[
                        "port",
                        "status",
                        "service",
                        "banner"
                    ]
                )

                writer.writeheader()
                writer.writerows(self.results)

            messagebox.showinfo(
                "Export Successful",
                f"Results exported successfully:\n{file_path}"
            )

        except OSError as error:
            messagebox.showerror(
                "Export Error",
                str(error)
            )


# ---------------- MAIN ----------------

if __name__ == "__main__":

    root = tk.Tk()

    app = PortScannerGUI(root)

    root.mainloop()