 <div align="center">

<img src="src/banner.png" alt="Network Programming and Engineering Projects Banner" width="100%">

# 🌐 Network Programming and Engineering Projects

### A Collection of Python Networking Projects

**Socket Programming | Network Analysis | Port Scanning | Real-Time Monitoring**

</div>

---

## 📌 About This Repository

This repository contains four hands-on Python projects focused on computer networking, socket programming, network traffic analysis, port scanning, and real-time network monitoring.

These projects demonstrate practical implementations of networking concepts, client-server communication, packet analysis, port scanning, and network performance monitoring.

## 🚀 Projects Overview

| No. | Project | Description |
|---|---|---|
| 01 | LAN Chat Application | Real-time communication using TCP sockets |
| 02 | Packet Sniffer | Capture and analyze network packets |
| 03 | Port Scanner | Identify open ports and test network connectivity |
| 04 | Network Monitoring Tool | Monitor network traffic and server availability |

---

## 1. LAN Chat Application

**Technologies:** Python, TCP Socket Programming, Threading

A client-server-based chat application that enables multiple users to communicate over a Local Area Network (LAN).

**Key Features:**
- TCP client-server communication.
- Multiple client connections.
- Thread-based concurrent communication.
- Real-time message broadcasting.
- Timestamped messages.
- Client connection and disconnection handling.
- `/quit` command to leave the chat.

**Project Folder:** `1. LAN Chat App`

---

## 2. Packet Sniffer

**Technologies:** Python, Scapy, Tkinter, Npcap

A graphical network packet analysis application that captures and displays live network traffic.

**Key Features:**
- Live network packet capture.
- TCP, UDP, ICMP, IPv4 and IPv6 packet classification.
- Protocol-based filtering.
- Packet details inspection.
- TCP flags, sequence numbers and acknowledgment numbers.
- Network packet statistics.
- Export captured packets to PCAP files.

**Project Folder:** `2. Packet Sniffer`

---

## 3. Port Scanner

**Technologies:** Python, Socket Programming, ThreadPoolExecutor, Tkinter

A network scanning application designed to identify open ports and examine TCP connectivity on a target host.

**Key Features:**
- Scan specified port ranges.
- Detect open ports.
- Identify closed and timed-out connections.
- Concurrent port scanning.
- Configurable connection timeout.
- Graphical user interface.
- Export scan results to CSV.

**Project Folder:** `3. Port Scanner`

---

## 4. Network Monitoring Tool

**Technologies:** Python, Tkinter, Psutil, Matplotlib, SQLite, Socket Programming

A real-time network monitoring desktop application that tracks network traffic, checks server connectivity, visualizes performance, and stores historical monitoring data.

**Key Features:**

- **Real-Time Network Monitoring:** Track upload speed, download speed, total data sent and received, and packet counts.
- **Live Performance Graphs:** Visualize upload and download speeds using Matplotlib.
- **Server Connectivity Testing:** Check server availability and measure TCP connection response time.
- **Automatic Server Monitoring:** Continuously monitor Google DNS, Cloudflare DNS, and Google Web.
- **Availability Tracking:** Calculate server availability based on successful and total monitoring checks.
- **SQLite Database:** Persist network statistics and server monitoring history.
- **Historical Data Viewer:** Retrieve and display previously stored monitoring records.
- **CSV Report Generation:** Export network statistics, server history, and availability reports.
- **Interactive GUI:** Dashboard with monitoring controls, event logs, and vertical scrolling.

**Project Folder:** `4. Network Monitoring Tool`

---

## 🛠️ Technologies and Concepts

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Networking | TCP/IP, Socket Programming |
| Concurrency | Threading, ThreadPoolExecutor |
| Packet Analysis | Scapy, Npcap |
| Network Monitoring | Psutil |
| Data Visualization | Matplotlib |
| GUI Development | Tkinter |
| Database | SQLite |
| Data Export | CSV |
| Version Control | Git, GitHub |

## 📂 Repository Structure

```text
Network_Programming_and_Engineering/
│
├── banner.png
│
├── 1. LAN Chat App/
│   ├── client.py
│   ├── server.py
│   └── README.md
│
├── 2. Packet Sniffer/
│   ├── sniffer_gui.py
│   ├── README.md
│   └── Other supporting files
│
├── 3. Port Scanner/
│   ├── port_scanner.py
│   ├── port_scanner_gui.py
│   ├── test_connection.py
│   └── README.md
│
├── 4. Network Monitoring Tool/
│   ├── realtime_mointer.py
│   ├── database.py
│   ├── check_database.py
│   ├── view_history.py
│   ├── export_database_reports.py
│   ├── requirements.txt
│   └── README.md
│
├── src/
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```


## ⚙️ Getting Started

### Prerequisites

- Python 3.10 or later.
- Visual Studio Code (recommended).
- Git.
- Npcap for packet capture on Windows (required by the Packet Sniffer).

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the Repository

```bash
cd Network_Programming_and_Engineering
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 4. Install Dependencies

Install the root-level dependencies:

```bash
pip install -r requirements.txt
```

Install any additional dependencies specified in the individual project folders.

## ▶️ Running the Projects

Navigate to the respective project folder before executing its entry-point file.

### LAN Chat Application

Terminal 1:

```bash
cd "1. LAN Chat App"
python server.py
```

Terminal 2:

```bash
python client.py
```

### Packet Sniffer

```bash
cd "2. Packet Sniffer"
python sniffer_gui.py
```

### Port Scanner

```bash
cd "3. Port Scanner"
python port_scanner_gui.py
```

### Network Monitoring Tool

```bash
cd "4. Network Monitoring Tool"
pip install -r requirements.txt
python database.py
python realtime_mointer.py
```

## 📊 Network Monitoring Database

The Network Monitoring Tool uses SQLite with two primary tables:

**1. network_history**

Stores:
- Timestamp.
- Upload and download speeds.
- Total bytes sent and received.
- Packets sent and received.

**2. server_history**

Stores:
- Timestamp.
- Server name and hostname.
- Port number.
- Connection status.
- Response time.
- Availability percentage.
- Total checks and failed checks.

### Export Monitoring Reports

```bash
python export_database_reports.py
```

Generated reports:
- `network_history_report.csv`
- `server_history_report.csv`


## 🎯 Learning Objectives

Through these projects, I explored and implemented:

- TCP client-server communication.
- Socket programming and network connections.
- Multithreading and concurrent processing.
- Network packet capture and protocol analysis.
- Port scanning and connectivity testing.
- Real-time network traffic monitoring.
- Server availability and response-time measurement.
- Database integration and historical data management.
- Graphical user interface development.
- Data export and reporting.

## 🔮 Future Enhancements

- Advanced network traffic analytics.
- Additional packet filtering and analysis capabilities.
- Improved port scanning performance.
- Network interface selection.
- Server downtime alerts.
- Advanced historical performance visualization.
