import socket
import random
import json
import threading
import sys
import select
from collections import defaultdict
import ipaddress

def constructMessage(type, msg, name, myIP, mac, destinationName, destinationMac = "", destinationIp = ""):
    data = {}
    data["type"] = type
    data["message"] = msg
    data["sourceName"] = name
    data["sourceIP"] = myIP
    data["sourceMac"] = mac
    data["destinationName"] = destinationName
    data["destinationMac"] = destinationMac
    data["destinationIp"] = destinationIp
    return json.dumps(data)

def is_ip_in_range(ip, subnet, ip_to_check):
    network = ipaddress.IPv4Network(f"{ip}/{subnet}", strict=False)
    return ipaddress.IPv4Address(ip_to_check) in network
    
def findHop(ip, table):
    for x in table:
        if(is_ip_in_range(x, table[x][1], ip)):
            return [x] + table[x]
    return ['0.0.0.0'] + table['0.0.0.0']

def findIPandConn(ips, sockets, iface):
    if(iface not in ips):
        iface = list(ips.keys())[0]
    return (ips[iface], sockets[iface])     
def findChain(hop, mapping):
    for x in mapping:
        if(mapping[x]==hop):
            return x
def findConnection(bridge, sockets):
    if(bridge in sockets):
        return sockets[bridge]
    return sockets[list(sockets.keys())[0]]

def processCommands(sockets,name, ips, mac, info, mapping, table, macMapping, pendingMessages, mapping_lock, messages_lock):
    print("Enter Your commands : ")
    while(True):
        try:
            command = input().split()
            if(command[0]=="show"):
                if(command[1]=="arp"):
                    print(macMapping)
                elif(command[1]=="pq"):
                    print(pendingMessages)
                elif(command[1]=="host"):
                    print(mapping)
                elif(command[1]=="iface"):
                    print(info)
                elif(command[1]=="rtable"):
                    print(table)
            elif(command[0]=="quit"):
                    break
            elif(command[0]=="send"):
                destinationName, msg = command[1], " ".join(command[2:])

                destinationName = destinationName.strip()
                destinationIp = mapping[destinationName]
                tempName = destinationName + info[0]["bridge"]
                if(tempName in mapping):
                    destinationIp = mapping[tempName]

                
                hop = findHop(destinationIp, table)
                myIP, conn = findIPandConn(ips, sockets, hop[3][1:])
                if(hop[1]=='0.0.0.0'):
                    with mapping_lock and messages_lock:    
                        if(destinationName not in macMapping):
                            constructArpReq = constructMessage("ARP REQ", "", name, myIP, mac, destinationName, "", destinationIp)
                            conn.sendall(constructArpReq.encode())
                            msgPacket = constructMessage("MSG", msg, name, myIP, mac, destinationName, "", destinationIp)
                            pendingMessages[destinationName].append((msgPacket, conn))
                        else:
                            msgPacket = constructMessage("MSG", msg, name, myIP, mac, destinationName, macMapping[destinationName], destinationIp)
                            conn.sendall(msgPacket.encode())
                else:
                    msgPacket = constructMessage("HOP", msg, name, myIP, mac, destinationName, "", destinationIp)
                    msgPacket = json.loads(msgPacket)
                    msgPacket["nextHop"] = hop[1]
                    chain = findChain(hop[1], mapping)
                    router, bridge = chain.split("-")
                    msgPacket["nextRouter"] = router
                    conn = findConnection(bridge, sockets)
                    conn.sendall(json.dumps(msgPacket).encode())
                    # socket.sendall(msgPacket.encode())
        except Exception as e:
            print(e)
            continue
            
def processMessage(s, data, macMapping, pendingMessages, mapping_lock, messages_lock, name, ips, mac, info, mapping):
    data = json.loads(data.decode())
    
    if(data["type"] == "ARP RES"):
        with mapping_lock and messages_lock:
            macMapping[data["sourceName"]] = data["sourceMac"]
            while(pendingMessages[data["sourceName"]]):
                elem = json.loads(pendingMessages[data["sourceName"]][0][0])
                conn = pendingMessages[data["sourceName"]][0][1]
                
                elem["destinationMac"] = data["sourceMac"]
                conn.sendall(json.dumps(elem).encode())
                pendingMessages[data["sourceName"]].pop(0)

    elif(data["type"] == "ARP REQ"):
        constructArpRes = constructMessage("ARP RES", "", name, data["destinationIp"], mac, data["sourceName"], data["sourceMac"] ,data["sourceIP"])
        s.sendall(constructArpRes.encode())
    else:
        print(data["sourceName"], " : ",data["message"])
        
def load_port_from_json(fileName):
    try:
        with open(fileName+".json", "r") as json_file:
            data = json.load(json_file)
            return data.get("port")
    except FileNotFoundError:
        return None 
        
def findIP(info):
    ipMapping = {}
    for x in info:
        ipMapping[x['bridge']] = x['IP']
    return ipMapping
    
def startConnections(info):
    connections = {}
    for x in info:
        fileName = x['bridge']
        HOST = "127.0.0.1"
        PORT = load_port_from_json(fileName)
        connections[fileName] = PORT
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(HOST,PORT)
        s.connect((HOST, PORT))
        s.sendall(info[0]['name'][:1].encode())
        connections[fileName] = s
    return connections    

def Client(info, mapping, table):
    name = info[0]['name'][:1]
    ips = findIP(info)
    mac = info[0]['mac']
    sockets = startConnections(info)
    #Resiurces for messaging
    macMapping = defaultdict(str)
    pendingMessages = defaultdict(list)
    mapping_lock = threading.Lock()
    messages_lock = threading.Lock()

        
    #Create a thread for sending messages
    send_thread = threading.Thread(target=processCommands, args=(sockets,name, ips, mac, info, mapping, table, macMapping, pendingMessages, mapping_lock, messages_lock))
    send_thread.start()
    
    while True:
        try:
            for i in sockets:
                s = sockets[i]
                s.settimeout(0.5)
                try:
                    data = s.recv(1024)
                    if(data.decode()=="accept"):
                        clientPort = s.getsockname()[1]
                        print("Client listening on ",s.getsockname())
                    elif(data.decode()=="reject"):
                        print("Connection Rejected")
                    elif not data:
                        s.close()
                        print("Server closed connection. Exiting.")
                        break
                    else:
                        processMessage(s, data, macMapping, pendingMessages, mapping_lock, messages_lock, name, ips, mac, info, mapping)
                except socket.timeout:
                    continue
        except socket.error as e:
            s.close()
            print("Socket error:", e)
            
def readHost(path):
    data = {}
    with open("./"+ path,"r") as file:
        for l in file:
            s = l.split()
            data[s[0]] = s[1]
    return data
def readIfaces(path):
    totalData = []
    with open("./ifaces/"+ path,"r") as file:
        for l in file:
            data = {}
            s = l.split()
            data["name"] = s[0]
            data["IP"] = s[1]
            data["mask"] = s[2]
            data["mac"] = s[3]
            data["bridge"] = s[4]
            totalData.append(data)
    return totalData
def readRoutingTables(path):
    data = {}
    with open("./rtables/" + path, "r") as file:
        for l in file:
            s = l.split()
            data[s[0]] = [s[1],s[2],s[3]]
    return data

if __name__=="__main__":
    print(sys.argv)
    iface,rtable,hosts = sys.argv[1:]
    stationInfo = readIfaces(iface)
    rTable = readRoutingTables(rtable)
    ipMapping = readHost(hosts)
    Client(stationInfo, ipMapping, rTable)