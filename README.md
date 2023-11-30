# Network-Emulator
# Project 2: Network Emulator

## Team Members
- [Your Name]
- [Team Member's Name (if applicable)]

## Project Overview
The Network Emulator project involves developing a network emulator with two components: the implementation of the emulator and a research-style report. The emulator simulates networking devices such as bridges, switches, and routers. The report details the design, development, and evaluation of the emulator.

### Project Objectives
1. Mastering socket-based networking application development.
2. Understanding functionalities of networking devices like bridges, switches, and routers.
3. Understanding packet forwarding in networks.
4. Experiencing team software development.
5. Writing a research-style paper.

### Components
#### Component 1: Network Emulator Development (Worth 20%)
- **Section I: Network Model Overview**
  - Broadcast Ethernet LANs with shared physical medium.
  - Star-wired LAN topology using transparent bridges (or switches).
  - IP routers interconnecting LANs to form an IP internetwork.

- **Section II: Computer Network Emulation**
  - Implementation using client-server socket programming.
  - Bridges as servers, stations (routers) as clients.
  - TCP socket connection emulation for physical links.

- **Section III: Network Components**
  - **Bridge**
    - Command line arguments: `lan-name` and `num-ports`.
    - Accepting connection requests, broadcasting frames, self-learning.
  - **Station**
    - Command line arguments: `interface`, `routingtable`, and `hostname`.
    - Loading configuration files, connecting to LANs, handling data frames.

- **Section IV: Provided Code**
  - Executable code and template.
  - Project template code for C/C++, Java, or Python.