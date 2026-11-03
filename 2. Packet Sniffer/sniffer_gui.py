from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, wrpcap
from scapy.layers.inet6 import _ICMPv6

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

import threading
from datetime import datetime


# ==========================================
# NETWORK CONFIGURATION
# ==========================================

INTERFACE = r"\Device\NPF_{2D4F77AC-EB96-48EC-8429-B828CD6947EF}"

running = False


# ==========================================
# PACKET STORAGE
# ==========================================

captured_packets = []
packets_lock = threading.Lock()


# ==========================================
# PACKET STATISTICS
# ==========================================

stats = {
    "Total": 0,
    "TCP": 0,
    "UDP": 0,
    "ICMP": 0,
    "Other": 0
}

stats_lock = threading.Lock()

packet_details = {}


# ==========================================
# UPDATE STATISTICS DASHBOARD
# ==========================================

def update_statistics():

    with stats_lock:
        current_stats = stats.copy()

    total_label.config(
        text=f"Total Packets: {current_stats['Total']}"
    )

    tcp_label.config(
        text=f"TCP: {current_stats['TCP']}"
    )

    udp_label.config(
        text=f"UDP: {current_stats['UDP']}"
    )

    icmp_label.config(
        text=f"ICMP: {current_stats['ICMP']}"
    )

    other_label.config(
        text=f"Other: {current_stats['Other']}"
    )


# ==========================================
# RESET STATISTICS
# ==========================================

def reset_statistics():

    with stats_lock:
        for key in stats:
            stats[key] = 0

    update_statistics()

    display_packet(
        "[+] Statistics reset successfully.\n"
    )


# ==========================================
# PROCESS NETWORK PACKETS
# ==========================================

def process_packet(packet):

    timestamp = datetime.now().strftime("%H:%M:%S")

    source_ip = "-"
    destination_ip = "-"

    source_port = "-"
    destination_port = "-"

    # Store captured packet for PCAP export

    with packets_lock:
        captured_packets.append(packet.copy())

    # Identify IPv4 packets

    if packet.haslayer(IP):

        ip = packet[IP]

        source_ip = ip.src
        destination_ip = ip.dst

    # Identify IPv6 packets

    elif packet.haslayer(IPv6):

        ip = packet[IPv6]

        source_ip = ip.src
        destination_ip = ip.dst

    # Identify TCP packets

    if packet.haslayer(TCP):

        protocol = "TCP"

        source_port = packet[TCP].sport
        destination_port = packet[TCP].dport

    # Identify UDP packets

    elif packet.haslayer(UDP):

        protocol = "UDP"

        source_port = packet[UDP].sport
        destination_port = packet[UDP].dport

    # Identify ICMP and ICMPv6 packets

    elif packet.haslayer(ICMP) or packet.haslayer(_ICMPv6):

        protocol = "ICMP"

    # Identify other protocols

    else:

        protocol = "Other"

    # Update packet statistics

    with stats_lock:

        stats["Total"] += 1
        stats[protocol] += 1

    # Prepare packet information

    if protocol in ("TCP", "UDP"):

        line = (
            f"[{timestamp}] {protocol} | "
            f"{source_ip}:{source_port} -> "
            f"{destination_ip}:{destination_port}\n"
        )

    else:

        line = (
            f"[{timestamp}] {protocol} | "
            f"{source_ip} -> {destination_ip}\n"
        )

    # Extract TCP details

    if protocol == "TCP":

        tcp_layer = packet[TCP]

        tcp_flags = str(tcp_layer.flags)

        sequence_number = tcp_layer.seq

        acknowledgment_number = tcp_layer.ack

        window_size = tcp_layer.window

    else:

        tcp_flags = "N/A"

        sequence_number = "N/A"

        acknowledgment_number = "N/A"

        window_size = "N/A"

    # Store detailed packet information

    details = {
        "Timestamp": timestamp,
        "Protocol": protocol,
        "Source IP": source_ip,
        "Destination IP": destination_ip,
        "Source Port": source_port,
        "Destination Port": destination_port,
        "Packet Length": f"{len(packet)} bytes",
        "TCP Flags": tcp_flags,
        "Sequence Number": sequence_number,
        "Acknowledgment Number": acknowledgment_number,
        "Window Size": window_size
    }

    # Update GUI safely

    root.after(
        0,
        display_filtered_packet,
        line,
        protocol,
        details
    )

    root.after(
        0,
        update_statistics
    )


# ==========================================
# DISPLAY PACKETS IN GUI
# ==========================================

def display_packet(message, details=None):

    line_number = output_box.index("end-1c").split(".")[0]

    output_box.insert(
        tk.END,
        message
    )

    if details is not None:

        packet_details[line_number] = details

    output_box.see(tk.END)


# ==========================================
# DISPLAY FILTERED PACKETS
# ==========================================

def display_filtered_packet(message, protocol, details):

    selected = selected_protocol.get()

    if selected == "All" or selected == protocol:

        display_packet(message, details)


# ==========================================
# SHOW SELECTED PACKET DETAILS
# ==========================================

def show_packet_details(event):

    clicked_position = output_box.index(
        f"@{event.x},{event.y}"
    )

    line_number = clicked_position.split(".")[0]

    details = packet_details.get(line_number)

    if not details:
        return

    details_text = "\n".join(
        f"{key}: {value}"
        for key, value in details.items()
    )

    details_window = tk.Toplevel(root)

    details_window.title("Packet Details")

    details_window.geometry("450x420")

    details_window.resizable(False, False)

    heading = tk.Label(
        details_window,
        text="Packet Analysis",
        font=("Arial", 16, "bold")
    )

    heading.pack(pady=15)

    details_label = tk.Label(
        details_window,
        text=details_text,
        font=("Arial", 11),
        justify=tk.LEFT,
        anchor="w"
    )

    details_label.pack(
        padx=25,
        pady=10,
        anchor="w"
    )

    close_button = tk.Button(
        details_window,
        text="Close",
        command=details_window.destroy,
        width=12
    )

    close_button.pack(pady=15)


# ==========================================
# EXPORT PACKETS TO PCAP
# ==========================================

def export_pcap():

    with packets_lock:
        packets_to_save = captured_packets.copy()

    if not packets_to_save:

        messagebox.showwarning(
            "No Packets",
            "No packets available to export. Start sniffing first."
        )

        return

    filename = filedialog.asksaveasfilename(
        title="Save Packet Capture",
        defaultextension=".pcap",
        filetypes=[
            ("PCAP Files", "*.pcap"),
            ("All Files", "*.*")
        ],
        initialfile=f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"
    )

    if not filename:
        return

    try:

        wrpcap(
            filename,
            packets_to_save
        )

        messagebox.showinfo(
            "Export Successful",
            f"Successfully exported {len(packets_to_save)} packets!\n\n"
            f"Saved to:\n{filename}"
        )

        display_packet(
            f"[+] Exported {len(packets_to_save)} packets to PCAP.\n"
        )

    except Exception as error:

        messagebox.showerror(
            "Export Error",
            str(error)
        )


# ==========================================
# PACKET SNIFFING
# ==========================================

def sniff_packets():

    try:

        root.after(
            0,
            display_packet,
            f"[+] Packet Sniffer started!\n"
            f"[+] Interface: {INTERFACE}\n\n"
        )

        sniff(
            iface=INTERFACE,
            prn=process_packet,
            store=False,
            stop_filter=lambda packet: not running
        )

        root.after(
            0,
            display_packet,
            "[+] Packet capture stopped.\n"
        )

    except Exception as error:

        root.after(
            0,
            display_packet,
            f"[ERROR] {error}\n"
        )


# ==========================================
# START SNIFFING
# ==========================================

def start_sniffing():

    global running

    if running:
        return

    running = True

    threading.Thread(
        target=sniff_packets,
        daemon=True
    ).start()


# ==========================================
# STOP SNIFFING
# ==========================================

def stop_sniffing():

    global running

    if not running:
        return

    running = False

    display_packet(
        "\n[+] Stopping packet capture...\n"
    )


# ==========================================
# MAIN GUI WINDOW
# ==========================================

root = tk.Tk()

root.title("Windows Network Packet Sniffer")

root.geometry("1000x700")

selected_protocol = tk.StringVar(value="All")


# ==========================================
# APPLICATION TITLE
# ==========================================

title = tk.Label(
    root,
    text="Network Packet Sniffer",
    font=("Arial", 18, "bold")
)

title.pack(pady=10)


# ==========================================
# STATISTICS DASHBOARD
# ==========================================

stats_frame = tk.LabelFrame(
    root,
    text="Packet Statistics",
    font=("Arial", 11, "bold"),
    padx=10,
    pady=10
)

stats_frame.pack(
    fill=tk.X,
    padx=15,
    pady=10
)


total_label = tk.Label(
    stats_frame,
    text="Total Packets: 0",
    font=("Arial", 12, "bold")
)

total_label.pack()


tcp_label = tk.Label(
    stats_frame,
    text="TCP: 0",
    font=("Arial", 11)
)

tcp_label.pack(side=tk.LEFT, padx=25)


udp_label = tk.Label(
    stats_frame,
    text="UDP: 0",
    font=("Arial", 11)
)

udp_label.pack(side=tk.LEFT, padx=25)


icmp_label = tk.Label(
    stats_frame,
    text="ICMP: 0",
    font=("Arial", 11)
)

icmp_label.pack(side=tk.LEFT, padx=25)


other_label = tk.Label(
    stats_frame,
    text="Other: 0",
    font=("Arial", 11)
)

other_label.pack(side=tk.LEFT, padx=25)


# ==========================================
# PROTOCOL FILTER
# ==========================================

filter_frame = tk.Frame(root)

filter_frame.pack(pady=5)


filter_label = tk.Label(
    filter_frame,
    text="Protocol Filter:",
    font=("Arial", 11, "bold")
)

filter_label.pack(side=tk.LEFT, padx=5)


protocol_filter = ttk.Combobox(
    filter_frame,
    textvariable=selected_protocol,
    values=["All", "TCP", "UDP", "ICMP", "Other"],
    state="readonly",
    width=15
)

protocol_filter.pack(side=tk.LEFT, padx=5)

protocol_filter.current(0)


# ==========================================
# PACKET DISPLAY AREA
# ==========================================

output_box = scrolledtext.ScrolledText(
    root,
    height=22,
    width=110,
    cursor="arrow"
)

output_box.pack(
    padx=15,
    pady=10,
    fill=tk.BOTH,
    expand=True
)

output_box.bind(
    "<Double-Button-1>",
    show_packet_details
)


# ==========================================
# BUTTON FRAME
# ==========================================

button_frame = tk.Frame(root)

button_frame.pack(pady=10)


start_button = tk.Button(
    button_frame,
    text="Start Sniffing",
    command=start_sniffing,
    bg="green",
    fg="white",
    width=15
)

start_button.pack(side=tk.LEFT, padx=8)


stop_button = tk.Button(
    button_frame,
    text="Stop Sniffing",
    command=stop_sniffing,
    bg="red",
    fg="white",
    width=15
)

stop_button.pack(side=tk.LEFT, padx=8)


reset_button = tk.Button(
    button_frame,
    text="Reset Statistics",
    command=reset_statistics,
    bg="blue",
    fg="white",
    width=15
)

reset_button.pack(side=tk.LEFT, padx=8)


export_button = tk.Button(
    button_frame,
    text="Export PCAP",
    command=export_pcap,
    bg="purple",
    fg="white",
    width=15
)

export_button.pack(side=tk.LEFT, padx=8)


# ==========================================
# CLOSE APPLICATION
# ==========================================

def close_application():

    global running

    running = False

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# ==========================================
# START APPLICATION
# ==========================================

root.mainloop()
