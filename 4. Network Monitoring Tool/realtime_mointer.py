
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import psutil
import time
import threading
import socket
import csv
import sqlite3

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import initialize_database, save_network_data, save_server_data


# ==================================================
# CONFIGURATION
# ==================================================

SOCKET_TIMEOUT = 3
MONITOR_INTERVAL = 5
GRAPH_POINTS = 30

DEFAULT_SERVERS = [
    ("Google DNS", "8.8.8.8", 53),
    ("Cloudflare DNS", "1.1.1.1", 53),
    ("Google Web", "google.com", 443),
]


# ==================================================
# SERVER CONNECTIVITY CHECK
# ==================================================

def check_server(host, port):

    start_time = time.perf_counter()

    try:
        with socket.create_connection(
            (host, port),
            timeout=SOCKET_TIMEOUT
        ):
            response_time = (
                time.perf_counter() - start_time
            ) * 1000

            return {
                "host": host,
                "port": port,
                "status": "ONLINE",
                "response_time": round(response_time, 2),
                "error": "-"
            }

    except (socket.timeout, TimeoutError):

        return {
            "host": host,
            "port": port,
            "status": "TIMEOUT",
            "response_time": None,
            "error": "Connection timed out"
        }

    except OSError as error:

        return {
            "host": host,
            "port": port,
            "status": "OFFLINE",
            "response_time": None,
            "error": str(error)
        }


# ==================================================
# REAL-TIME NETWORK MONITOR
# ==================================================

class RealTimeMonitor:

    def __init__(self, ui):

        self.ui = ui
        self.running = False
        self.monitor_thread = None

        self.prev = psutil.net_io_counters()

    def start(self):

        if self.running:
            return

        self.running = True
        self.prev = psutil.net_io_counters()

        self.monitor_thread = threading.Thread(
            target=self.update_loop,
            daemon=True
        )

        self.monitor_thread.start()

        self.ui.schedule_ui(
            lambda: self.ui.log(
                "Real-time network monitoring started."
            )
        )

    def stop(self):

        if not self.running:
            return

        self.running = False

        self.ui.schedule_ui(
            lambda: self.ui.log(
                "Real-time network monitoring stopped."
            )
        )

    def update_loop(self):

        previous_time = time.monotonic()

        while self.running:

            time.sleep(1)

            if not self.running:
                break

            current_time = time.monotonic()
            elapsed = current_time - previous_time

            now = psutil.net_io_counters()

            upload_speed = (
                now.bytes_sent - self.prev.bytes_sent
            ) / elapsed

            download_speed = (
                now.bytes_recv - self.prev.bytes_recv
            ) / elapsed

            packets_sent = (
                now.packets_sent - self.prev.packets_sent
            )

            packets_recv = (
                now.packets_recv - self.prev.packets_recv
            )

            self.prev = now
            previous_time = current_time

            self.ui.schedule_ui(
                lambda up=upload_speed,
                       down=download_speed,
                       total_up=now.bytes_sent,
                       total_down=now.bytes_recv,
                       sent=packets_sent,
                       received=packets_recv:

                self.ui.update_stats(
                    up,
                    down,
                    total_up,
                    total_down,
                    sent,
                    received
                )
            )


# ==================================================
# AUTOMATIC SERVER MONITOR
# ==================================================

class AutomaticServerMonitor:

    def __init__(self, ui):

        self.ui = ui
        self.running = False
        self.stop_event = threading.Event()
        self.monitor_thread = None

        self.history = {}

        for name, host, port in DEFAULT_SERVERS:

            self.history[name] = {
                "total_checks": 0,
                "successful_checks": 0,
                "failed_checks": 0,
                "previous_status": None,
                "downtime_start": None
            }

    def start(self):

        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            daemon=True
        )

        self.monitor_thread.start()

        self.ui.schedule_ui(
            lambda: self.ui.log(
                "Automatic server monitoring started."
            )
        )

    def stop(self):

        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        self.ui.schedule_ui(
            lambda: self.ui.log(
                "Automatic server monitoring stopped."
            )
        )

    def monitor_loop(self):

        with ThreadPoolExecutor(max_workers=3) as executor:

            while not self.stop_event.is_set():

                futures = {}

                for name, host, port in DEFAULT_SERVERS:

                    future = executor.submit(
                        check_server,
                        host,
                        port
                    )

                    futures[future] = (name, host, port)

                results = []

                for future, details in futures.items():

                    name, host, port = details

                    if self.stop_event.is_set():
                        break

                    try:
                        result = future.result(
                            timeout=SOCKET_TIMEOUT + 1
                        )

                    except Exception as error:

                        result = {
                            "host": host,
                            "port": port,
                            "status": "ERROR",
                            "response_time": None,
                            "error": str(error)
                        }

                    result["name"] = name

                    self.update_history(name, result)

                    results.append(result)

                if results and not self.stop_event.is_set():

                    self.ui.schedule_ui(
                        lambda data=results:
                        self.ui.update_server_monitor(data)
                    )

                self.stop_event.wait(MONITOR_INTERVAL)

    def update_history(self, name, result):

        record = self.history[name]
        status = result["status"]

        record["total_checks"] += 1

        if status == "ONLINE":

            record["successful_checks"] += 1

            if record["previous_status"] not in (
                None, "ONLINE"
            ):

                if record["downtime_start"] is not None:

                    downtime = (
                        time.monotonic()
                        - record["downtime_start"]
                    )

                    result["event"] = (
                        f"{name} recovered after "
                        f"{downtime:.1f} seconds."
                    )

                    record["downtime_start"] = None

        else:

            record["failed_checks"] += 1

            if record["previous_status"] == "ONLINE":

                record["downtime_start"] = time.monotonic()

                result["event"] = (
                    f"{name} is now {status}."
                )

            elif record["previous_status"] is None:

                result["event"] = (
                    f"{name} initial status: {status}."
                )

        record["previous_status"] = status

        result["availability"] = round(
            record["successful_checks"]
            / record["total_checks"] * 100,
            2
        )

        result["total_checks"] = record["total_checks"]
        result["failed_checks"] = record["failed_checks"]


# ==================================================
# MAIN GUI APPLICATION
# ==================================================

class MonitorUI:

    def __init__(self, root):

        self.root = root
        self.closing = False

        # Initialize persistent SQLite storage
        initialize_database()

        # CSV history
        self.network_history = []
        self.server_history = []

        # Network graph history
        self.time_points = deque(maxlen=GRAPH_POINTS)
        self.upload_points = deque(maxlen=GRAPH_POINTS)
        self.download_points = deque(maxlen=GRAPH_POINTS)

        self.graph_counter = 0

        # Server response-time history
        self.server_response_times = {
            name: deque(maxlen=GRAPH_POINTS)
            for name, host, port in DEFAULT_SERVERS
        }

        self.executor = ThreadPoolExecutor(max_workers=5)

        self.monitor = RealTimeMonitor(self)
        self.server_monitor = AutomaticServerMonitor(self)

        root.title("Network Monitoring Tool")
        root.geometry("950x700")
        root.minsize(800, 600)

        self.create_widgets()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

    # ------------------------------------------------
    # THREAD-SAFE GUI SCHEDULER
    # ------------------------------------------------

    def schedule_ui(self, callback):

        if not self.closing:

            try:
                self.root.after(0, callback)

            except tk.TclError:
                pass

    # ------------------------------------------------
    # GUI DESIGN
    # ------------------------------------------------

    def create_widgets(self):

        # Scrollable dashboard container
        outer_frame = ttk.Frame(self.root)
        outer_frame.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(
            outer_frame,
            highlightthickness=0,
            borderwidth=0
        )

        scrollbar = ttk.Scrollbar(
            outer_frame,
            orient="vertical",
            command=self.scroll_canvas.yview
        )

        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        # All dashboard widgets are placed inside this frame.
        self.scrollable_frame = ttk.Frame(self.scroll_canvas)
        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            self._update_scroll_region
        )
        self.scroll_canvas.bind(
            "<Configure>",
            self._resize_scrollable_frame
        )

        # Enable mouse-wheel scrolling while the pointer is over the dashboard.
        self.scroll_canvas.bind("<Enter>", self._bind_mousewheel)
        self.scroll_canvas.bind("<Leave>", self._unbind_mousewheel)

        main_frame = ttk.Frame(
            self.scrollable_frame,
            padding=15
        )
        main_frame.pack(fill="both", expand=True)

        title = ttk.Label(
            main_frame,
            text="NETWORK MONITORING DASHBOARD",
            font=("Arial", 20, "bold")
        )

        title.pack(pady=10)

        # REAL-TIME CONTROLS

        control_frame = ttk.LabelFrame(
            main_frame,
            text="Real-Time Network Monitoring",
            padding=10
        )

        control_frame.pack(fill="x", pady=8)

        self.start_button = ttk.Button(
            control_frame,
            text="Start Monitoring",
            command=self.start_monitor
        )

        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop Monitoring",
            command=self.stop_monitor,
            state="disabled"
        )

        self.stop_button.grid(row=0, column=1, padx=10)

        # NETWORK STATISTICS

        stats_frame = ttk.LabelFrame(
            main_frame,
            text="Network Statistics",
            padding=10
        )

        stats_frame.pack(fill="x", pady=8)

        labels = [
            "Upload Speed:",
            "Download Speed:",
            "Total Data Sent:",
            "Total Data Received:",
            "Packets Sent:",
            "Packets Received:"
        ]

        self.values = {}

        for i, label in enumerate(labels):

            ttk.Label(
                stats_frame,
                text=label
            ).grid(
                row=i,
                column=0,
                sticky="w",
                padx=10,
                pady=4
            )

            variable = tk.StringVar(value="0")

            ttk.Label(
                stats_frame,
                textvariable=variable,
                font=("Arial", 10, "bold")
            ).grid(
                row=i,
                column=1,
                sticky="w",
                padx=10,
                pady=4
            )

            self.values[label] = variable

        # LIVE NETWORK GRAPHS

        graph_frame = ttk.LabelFrame(
            main_frame,
            text="Live Network Performance Graphs",
            padding=10
        )

        graph_frame.pack(
            fill="both",
            expand=True,
            pady=8
        )

        self.figure = Figure(
            figsize=(8, 4.2),
            dpi=90
        )

        self.ax_network = self.figure.add_subplot(211)

        self.ax_network.set_title(
            "Upload and Download Speed"
        )

        self.ax_network.set_ylabel("Speed (KB/s)")
        self.ax_network.set_xlabel("Time (seconds)")
        self.ax_network.grid(True)

        self.ax_server = self.figure.add_subplot(212)

        self.ax_server.set_title(
            "Server Response Time"
        )

        self.ax_server.set_ylabel("Response Time (ms)")
        self.ax_server.set_xlabel("Monitoring Interval")
        self.ax_server.grid(True)

        self.figure.tight_layout()

        self.graph_canvas = FigureCanvasTkAgg(
            self.figure,
            master=graph_frame
        )

        self.graph_canvas.draw()

        self.graph_canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        # MANUAL CONNECTIVITY

        manual_frame = ttk.LabelFrame(
            main_frame,
            text="Manual Server Connectivity Check",
            padding=10
        )

        manual_frame.pack(fill="x", pady=8)

        ttk.Label(
            manual_frame,
            text="Host / IP:"
        ).grid(row=0, column=0, padx=5)

        self.host_entry = ttk.Entry(
            manual_frame,
            width=25
        )

        self.host_entry.grid(row=0, column=1, padx=5)
        self.host_entry.insert(0, "google.com")

        ttk.Label(
            manual_frame,
            text="Port:"
        ).grid(row=0, column=2, padx=5)

        self.port_entry = ttk.Entry(
            manual_frame,
            width=10
        )

        self.port_entry.grid(row=0, column=3, padx=5)
        self.port_entry.insert(0, "443")

        self.check_button = ttk.Button(
            manual_frame,
            text="Check Connection",
            command=self.check_connection
        )

        self.check_button.grid(row=0, column=4, padx=10)

        # AUTOMATIC SERVER MONITORING

        auto_frame = ttk.LabelFrame(
            main_frame,
            text="Automatic Continuous Server Monitoring",
            padding=10
        )

        auto_frame.pack(
            fill="both",
            expand=True,
            pady=8
        )

        button_frame = ttk.Frame(auto_frame)
        button_frame.pack(pady=5)

        self.auto_start_button = ttk.Button(
            button_frame,
            text="Start Automatic Monitoring",
            command=self.start_auto_monitor
        )

        self.auto_start_button.grid(row=0, column=0, padx=10)

        self.auto_stop_button = ttk.Button(
            button_frame,
            text="Stop Automatic Monitoring",
            command=self.stop_auto_monitor,
            state="disabled"
        )

        self.auto_stop_button.grid(row=0, column=1, padx=10)

        ttk.Label(
            auto_frame,
            text="Automatic checks run every 5 seconds."
        ).pack(pady=5)

        columns = (
            "Server",
            "Host",
            "Port",
            "Status",
            "Response Time",
            "Availability",
            "Total Checks",
            "Failed Checks"
        )

        self.server_tree = ttk.Treeview(
            auto_frame,
            columns=columns,
            show="headings",
            height=4
        )

        widths = [120, 120, 60, 90, 110, 100, 95, 95]

        for column, width in zip(columns, widths):

            self.server_tree.heading(column, text=column)

            self.server_tree.column(
                column,
                width=width,
                anchor="center"
            )

        self.server_tree.pack(
            fill="both",
            expand=True,
            pady=8
        )

        # CSV EXPORT BUTTONS

        export_frame = ttk.LabelFrame(
            auto_frame,
            text="Monitoring Reports",
            padding=10
        )

        export_frame.pack(fill="x", pady=5)

        ttk.Button(
            export_frame,
            text="Export Server History",
            command=self.export_server_history
        ).grid(row=0, column=0, padx=8)

        ttk.Button(
            export_frame,
            text="Export Network Statistics",
            command=self.export_network_history
        ).grid(row=0, column=1, padx=8)

        ttk.Button(
            export_frame,
            text="Export Availability Report",
            command=self.export_availability_report
        ).grid(row=0, column=2, padx=8)

        ttk.Button(
            export_frame,
            text="View Saved Database History",
            command=self.view_saved_history
        ).grid(row=1, column=0, columnspan=3, pady=8)

        # EVENT LOG

        ttk.Label(
            main_frame,
            text="Event Log:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        self.log_box = tk.Text(
            main_frame,
            height=5,
            state="disabled"
        )

        self.log_box.pack(fill="x", pady=5)

    # ------------------------------------------------
    # DASHBOARD SCROLLING
    # ------------------------------------------------

    def _update_scroll_region(self, event=None):
        self.scroll_canvas.configure(
            scrollregion=self.scroll_canvas.bbox("all")
        )

    def _resize_scrollable_frame(self, event):
        # Keep the content at least as wide as the visible canvas.
        self.scroll_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def _bind_mousewheel(self, event=None):
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.root.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event=None):
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # Windows uses multiples of 120; trackpads may send smaller values.
        if event.delta:
            self.scroll_canvas.yview_scroll(
                int(-event.delta / 120) if abs(event.delta) >= 120
                else (-1 if event.delta > 0 else 1),
                "units"
            )

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    # ------------------------------------------------
    # FORMATTING
    # ------------------------------------------------

    def format_speed(self, speed):

        if speed >= 1024 * 1024:
            return f"{speed / (1024 * 1024):.2f} MB/s"

        return f"{speed / 1024:.2f} KB/s"

    def format_bytes(self, size):

        units = ["B", "KB", "MB", "GB", "TB"]

        for unit in units:

            if size < 1024:
                return f"{size:.2f} {unit}"

            size /= 1024

        return f"{size:.2f} PB"

    # ------------------------------------------------
    # NETWORK STATISTICS AND GRAPH
    # ------------------------------------------------

    def update_stats(
        self,
        up,
        down,
        total_up,
        total_down,
        packets_sent,
        packets_recv
    ):

        self.network_history.append({
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "upload_speed_bytes_per_second": round(up, 2),
            "download_speed_bytes_per_second": round(down, 2),
            "total_bytes_sent": total_up,
            "total_bytes_received": total_down,
            "packets_sent": packets_sent,
            "packets_received": packets_recv
        })

        # Save each network sample to SQLite
        try:
            save_network_data(self.network_history[-1])
        except Exception as error:
            self.log(f"Database error (network data): {error}")

        self.values["Upload Speed:"].set(
            self.format_speed(up)
        )

        self.values["Download Speed:"].set(
            self.format_speed(down)
        )

        self.values["Total Data Sent:"].set(
            self.format_bytes(total_up)
        )

        self.values["Total Data Received:"].set(
            self.format_bytes(total_down)
        )

        self.values["Packets Sent:"].set(str(packets_sent))
        self.values["Packets Received:"].set(str(packets_recv))

        self.update_network_graph(up, down)

    def update_network_graph(self, upload_speed, download_speed):

        self.graph_counter += 1

        self.time_points.append(self.graph_counter)

        self.upload_points.append(upload_speed / 1024)
        self.download_points.append(download_speed / 1024)

        self.ax_network.clear()

        self.ax_network.plot(
            list(self.time_points),
            list(self.upload_points),
            label="Upload",
            marker="o"
        )

        self.ax_network.plot(
            list(self.time_points),
            list(self.download_points),
            label="Download",
            marker="o"
        )

        self.ax_network.set_title(
            "Upload and Download Speed"
        )

        self.ax_network.set_ylabel("Speed (KB/s)")
        self.ax_network.set_xlabel("Time (seconds)")
        self.ax_network.legend()
        self.ax_network.grid(True)

        self.graph_canvas.draw_idle()

    # ------------------------------------------------
    # SERVER RESPONSE GRAPH
    # ------------------------------------------------

    def update_server_graph(self, results):

        for result in results:

            name = result["name"]

            if name not in self.server_response_times:
                continue

            response_time = result["response_time"]

            self.server_response_times[name].append(
                response_time if response_time is not None else float("nan")
            )

        self.ax_server.clear()

        for name, response_times in self.server_response_times.items():

            if response_times:

                self.ax_server.plot(
                    range(1, len(response_times) + 1),
                    list(response_times),
                    marker="o",
                    label=name
                )

        self.ax_server.set_title("Server Response Time")
        self.ax_server.set_ylabel("Response Time (ms)")
        self.ax_server.set_xlabel("Monitoring Interval")
        self.ax_server.legend()
        self.ax_server.grid(True)

        self.graph_canvas.draw_idle()

    # ------------------------------------------------
    # REAL-TIME MONITOR CONTROLS
    # ------------------------------------------------

    def start_monitor(self):

        self.monitor.start()

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop_monitor(self):

        self.monitor.stop()

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    # ------------------------------------------------
    # MANUAL CONNECTIVITY CHECK
    # ------------------------------------------------

    def check_connection(self):

        host = self.host_entry.get().strip()
        port_text = self.port_entry.get().strip()

        if not host:

            messagebox.showerror(
                "Input Error",
                "Please enter a hostname or IP address."
            )

            return

        try:

            port = int(port_text)

            if not 1 <= port <= 65535:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Input Error",
                "Enter a valid port between 1 and 65535."
            )

            return

        self.check_button.config(state="disabled")

        self.log(f"Checking {host}:{port}...")

        future = self.executor.submit(
            check_server,
            host,
            port
        )

        future.add_done_callback(
            lambda f: self.schedule_ui(
                lambda: self.display_manual_result(f, host, port)
            )
        )

    def display_manual_result(self, future, host, port):

        try:

            result = future.result()

            response = (
                f"{result['response_time']} ms"
                if result["response_time"] is not None
                else "-"
            )

            self.log(
                f"{host}: {result['status']} | Response: {response}"
            )

        except Exception as error:

            self.log(f"Connectivity check error: {error}")

        finally:

            self.check_button.config(state="normal")

    # ------------------------------------------------
    # AUTOMATIC MONITOR CONTROLS
    # ------------------------------------------------

    def start_auto_monitor(self):

        self.server_monitor.start()

        self.auto_start_button.config(state="disabled")
        self.auto_stop_button.config(state="normal")

    def stop_auto_monitor(self):

        self.server_monitor.stop()

        self.auto_start_button.config(state="normal")
        self.auto_stop_button.config(state="disabled")

    # ------------------------------------------------
    # UPDATE SERVER TABLE AND HISTORY
    # ------------------------------------------------

    def update_server_monitor(self, results):

        for result in results:

            name = result["name"]

            self.server_history.append({
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "server": name,
                "host": result["host"],
                "port": result["port"],
                "status": result["status"],
                "response_time_ms": result["response_time"],
                "availability_percent": result["availability"],
                "total_checks": result["total_checks"],
                "failed_checks": result["failed_checks"]
            })

            # Save each server check to SQLite
            try:
                save_server_data(self.server_history[-1])
            except Exception as error:
                self.log(f"Database error (server data): {error}")

            response = (
                f"{result['response_time']} ms"
                if result["response_time"] is not None
                else "-"
            )

            row_values = (
                name,
                result["host"],
                result["port"],
                result["status"],
                response,
                f"{result['availability']}%",
                result["total_checks"],
                result["failed_checks"]
            )

            existing_item = None

            for item in self.server_tree.get_children():

                values = self.server_tree.item(item, "values")

                if values and values[0] == name:
                    existing_item = item
                    break

            if existing_item:

                self.server_tree.item(
                    existing_item,
                    values=row_values
                )

            else:

                self.server_tree.insert(
                    "",
                    tk.END,
                    values=row_values
                )

            if "event" in result:
                self.log(result["event"])

        self.update_server_graph(results)

    # ------------------------------------------------
    # CSV EXPORT FUNCTIONS
    # ------------------------------------------------

    def export_server_history(self):

        if not self.server_history:

            messagebox.showwarning(
                "No Data",
                "Please run automatic server monitoring first."
            )

            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="server_monitoring_history.csv"
        )

        if not file_path:
            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=self.server_history[0].keys()
                )

                writer.writeheader()
                writer.writerows(self.server_history)

            self.log("Server history exported successfully.")

            messagebox.showinfo(
                "Export Successful",
                f"Server history saved to:\n{file_path}"
            )

        except OSError as error:

            messagebox.showerror("Export Error", str(error))

    def export_network_history(self):

        if not self.network_history:

            messagebox.showwarning(
                "No Data",
                "Please start real-time network monitoring first."
            )

            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="network_statistics.csv"
        )

        if not file_path:
            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=self.network_history[0].keys()
                )

                writer.writeheader()
                writer.writerows(self.network_history)

            self.log("Network statistics exported successfully.")

            messagebox.showinfo(
                "Export Successful",
                f"Network statistics saved to:\n{file_path}"
            )

        except OSError as error:

            messagebox.showerror("Export Error", str(error))

    def export_availability_report(self):

        if not any(
            data["total_checks"] > 0
            for data in self.server_monitor.history.values()
        ):

            messagebox.showwarning(
                "No Data",
                "No server monitoring history is available."
            )

            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="server_availability_report.csv"
        )

        if not file_path:
            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                fields = [
                    "Server",
                    "Total Checks",
                    "Successful Checks",
                    "Failed Checks",
                    "Availability Percentage"
                ]

                writer = csv.DictWriter(
                    file,
                    fieldnames=fields
                )

                writer.writeheader()

                for name, data in self.server_monitor.history.items():

                    total = data["total_checks"]
                    successful = data["successful_checks"]
                    failed = data["failed_checks"]

                    availability = (
                        successful / total * 100
                        if total else 0
                    )

                    writer.writerow({
                        "Server": name,
                        "Total Checks": total,
                        "Successful Checks": successful,
                        "Failed Checks": failed,
                        "Availability Percentage": round(
                            availability, 2
                        )
                    })

            self.log("Availability report exported successfully.")

            messagebox.showinfo(
                "Export Successful",
                f"Availability report saved to:\n{file_path}"
            )

        except OSError as error:

            messagebox.showerror("Export Error", str(error))

    # ------------------------------------------------
    # VIEW PERSISTENT SQLITE HISTORY
    # ------------------------------------------------

    def view_saved_history(self):

        window = tk.Toplevel(self.root)
        window.title("Saved Monitoring History")
        window.geometry("1050x600")
        window.minsize(750, 450)

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        def create_history_tab(title, columns, query):
            frame = ttk.Frame(notebook, padding=8)
            notebook.add(frame, text=title)

            tree = ttk.Treeview(
                frame,
                columns=columns,
                show="headings",
                height=18
            )

            for column in columns:
                tree.heading(column, text=column.replace("_", " ").title())
                tree.column(column, width=140, minwidth=90, anchor="center")

            vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

            tree.grid(row=0, column=0, sticky="nsew")
            vertical.grid(row=0, column=1, sticky="ns")
            horizontal.grid(row=1, column=0, sticky="ew")
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)

            try:
                with sqlite3.connect("network_monitor.db") as connection:
                    rows = connection.execute(query).fetchall()
                for row in rows:
                    tree.insert("", tk.END, values=row)
                ttk.Label(
                    frame,
                    text=f"Showing {len(rows)} most recent saved records"
                ).grid(row=2, column=0, sticky="w", pady=(8, 0))
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", str(error), parent=window)

        create_history_tab(
            "Network History",
            ("timestamp", "upload_speed", "download_speed", "total_bytes_sent",
             "total_bytes_received", "packets_sent", "packets_received"),
            """SELECT timestamp, upload_speed, download_speed,
                      total_bytes_sent, total_bytes_received,
                      packets_sent, packets_received
               FROM network_history ORDER BY id DESC LIMIT 200"""
        )

        create_history_tab(
            "Server History",
            ("timestamp", "server_name", "host", "port", "status",
             "response_time", "availability", "total_checks", "failed_checks"),
            """SELECT timestamp, server_name, host, port, status,
                      response_time, availability, total_checks, failed_checks
               FROM server_history ORDER BY id DESC LIMIT 200"""
        )

    # ------------------------------------------------
    # EVENT LOG
    # ------------------------------------------------

    def log(self, message):

        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_box.config(state="normal")

        self.log_box.insert(
            tk.END,
            f"[{timestamp}] {message}\n"
        )

        self.log_box.see(tk.END)

        self.log_box.config(state="disabled")

    # ------------------------------------------------
    # CLOSE APPLICATION
    # ------------------------------------------------

    def close_application(self):

        self.closing = True

        self.monitor.stop()
        self.server_monitor.stop()

        self.executor.shutdown(
            wait=False,
            cancel_futures=True
        )

        self.root.destroy()


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = MonitorUI(root)

    root.mainloop()
