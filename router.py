import socket
import random
import json
import threading
import sys
import select
from collections import defaultdict
import ipaddress


def is_ip_in_range(ip, subnet, ip_to_check):
    network = ipaddress.IPv4Network(f"{ip}/{subnet}", strict=False)
    return ipaddress.IPv4Address(ip_to_check) in network
    
def findHop(ip, table):
    for x in table:
        if(is_ip_in_range(x, table[x][1], ip)):
            return [x] + table[x]
    return ['0.0.0.0'] + table['0.0.0.0']

def findChain(hop, mapping):
    for x in mapping:
        if(mapping[x]==hop):
            return x
            
def findConnection(bridge, sockets):
    if(bridge in sockets):
        return sockets[bridge]
    return sockets[list(sockets.keys())[0]]

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

def processMessage(sockets, data, name, mac, table, mapping, macMapping, pendingMessages):
    data = data.decode()
    data = json.loads(data)
    
    if(data["type"] == "ARP RES"):
        macMapping[data["sourceName"]] = data["sourceMac"]
        print(pendingMessages)
        while(pendingMessages[data["sourceName"]]):
            elem = json.loads(pendingMessages[data["sourceName"]][0][0])
            conn = pendingMessages[data["sourceName"]][0][1]
            print("----------------")
            print(elem)
            print("----------------")
                
            elem["destinationMac"] = data["sourceMac"]
            print("----------------")
            print(elem)
            print("----------------")
            conn.sendall(json.dumps(elem).encode())
            pendingMessages[data["sourceName"]].pop(0)
        return
        
    destinationIp = data["destinationIp"]

    hop = findHop(destinationIp, table)
    router, bridge = hop[3].split("-")
    conn = findConnection(bridge, sockets)
    print(hop,router,bridge)
    if(hop[1]=='0.0.0.0'):
        #ARP Request and all those things
        destinationName = data["destinationName"]
        if(destinationName not in macMapping):
            constructArpReq = constructMessage("ARP REQ", "", name, "", mac, data["destinationName"], "", data["destinationIp"])
            conn.sendall(constructArpReq.encode())

            data["type"] = "MSG"
            data["nextHop"] = ""
            data["nextRouter"] = ""
            
            data = json.dumps(data)
            pendingMessages[destinationName].append((data, conn))
        else:
            data["destinationMac"] = macMapping[destinationName]
            data["type"] = "MSG"
            data["nextHop"] = ""
            data["nextRouter"] = ""
            data = json.dumps(data)
            conn.sendall(data.encode())
    else:
        router, bridge = hop[3].split("-")
        conn = findConnection(bridge, sockets)
        data["nextHop"] = hop[1]
        data["nextRouter"] = router
                    
        print(router, bridge, conn, sockets, data)
        conn.sendall(json.dumps(data).encode())

def startConnections(info):
    connections = {}
    for x in info:
        fileName = x['bridge']
        HOST = "127.0.0.1"
        PORT = load_port_from_json(fileName)
        connections[fileName] = PORT
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        
        name =  info[0]['name'].split("-")[0]
        s.sendall(name.encode())
        
        connections[fileName] = s
    return connections    
def findIP(info):
    ipMapping = {}
    for x in info:
        ipMapping[x['bridge']] = x['IP']
    return ipMapping
def load_port_from_json(fileName):
    try:
        with open(fileName+".json", "r") as json_file:
            data = json.load(json_file)
            return data.get("port")
    except FileNotFoundError:
        return None 

def Client(info, mapping, table):
    name = info[0]['name'].split("-")[0]
    ips = findIP(info)
    mac = info[0]['mac']
    # print(name, ipMapping, mac)
    sockets = startConnections(info)
    macMapping = {}
    pendingMessages = defaultdict(list)

    while True:
        try:
            for i in sockets:
                s = sockets[i]
                s.settimeout(0.5)
                try:
                    data = s.recv(1024)
                    print(data)
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
                        processMessage(sockets, data, name, mac, table, mapping, macMapping, pendingMessages)
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