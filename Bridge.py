import socket
import select
import random
import json
import sys

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
        except socket.error:
            return False
    return True
def generate_random_port():
    while True:
        port = random.randint(1024, 65535)
        if is_port_available(port):
            return port
def processSendData(data, stationsConnections, stationsMapping):
    data = json.loads(data)
    if(data["type"] == "ARP REQ" or data["type"]=="ARP RES"):
        stationsMapping[data["sourceName"]] = data["sourceMac"]
        destinationName = data["destinationName"]
        print("ARP Req :", data)
        data = json.dumps(data)
        stationsConnections[destinationName].sendall(data.encode())
    else:
        if(data["destinationMac"]!=''):
            name = data["destinationName"]
            conn = stationsConnections[name]
            data = json.dumps(data)
            conn.sendall(data.encode())
        else:
            print(data)
            if("nextRouter" in data):
                conn = stationsConnections[data["nextRouter"]]
                conn.sendall(json.dumps(data).encode())
def save_port_to_json(fileName, port):
    data = {"port": port}
    with open(fileName + ".json", "w") as json_file:
        json.dump(data, json_file)
        
def Bridge(bridge_name, num_ports):
    HOST = "127.0.0.1"
    PORT = generate_random_port()
    save_port_to_json(bridge_name, PORT)
    print(f"{PORT} is available")
    
    stationsMapping = {} # Name to Mac Mapping
    stationsConnections = {} #Name to Socket Mapping
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server listening on {HOST}:{PORT}")

        # List to keep track of all connected clients
        client_sockets = [server_socket]
        
        while True:
            read_sockets, _, _ = select.select(client_sockets, [], [])
            for sock in read_sockets:
                
                if sock == server_socket:
                    # New connection, accept it
                    if(num_ports>0):
                        num_ports-=1
                        conn, addr = server_socket.accept()
                        print(f"Connected by {addr}")
                        client_sockets.append(conn)

                        #Recieve Name
                        name = conn.recv(1024)
                        name = name.decode()
        
                        stationsConnections[name] = conn
                        print(stationsConnections)
                        print(stationsMapping)

                        #Send Accpet message
                        conn.sendall(b'accept')
                    else:
                        conn, addr = server_socket.accept()
                        conn.sendall(b'reject')
                else:
                    # Existing connection, receive and echo back data
                    try:
                        data = sock.recv(1024)
                        data = data.decode()
                        if not data:
                            # Client disconnected
                            address = sock.getpeername()
                            print("Nothing on socket : ",address)
                            print(f"Connection closed by {address}")
                            client_sockets.remove(sock)
                            num_ports+=1
                        else:
                            processSendData(data, stationsConnections, stationsMapping)
                    except Exception as e:
                        print(e)
                        address = sock.getpeername()
                        print("Nothing on socket : ",address)
                        print(f"Connection closed by {address}")
                        client_sockets.remove(sock)
                        num_ports+=1
                        
if __name__=="__main__":
    bridge_name, num_ports = sys.argv[1:]
    num_ports = int(num_ports)
    Bridge(bridge_name, num_ports)