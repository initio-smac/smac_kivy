import asyncio
import socket
from smac_limits import STATE_CONNECTED_INTERNET, STATE_CONNECTED_NO_INTERNET, STATE_NO_CONNECTION

def update_network_connection():
    try:
        socket.settimeout(5)
        socket.create_connection(("www.google.com", 80))
        socket.settimeout(None)
        return STATE_CONNECTED_INTERNET
    except OSError:
        return STATE_NO_CONNECTION
    except:
        return STATE_CONNECTED_NO_INTERNET

class NetworkScanner:
    SCAN_IPS = []
    IS_SCANNING = False

    def get_hostname(self, ip):
        try:
            print(socket.gethostbyaddr(ip))
            return socket.gethostbyaddr(ip)[0]
        except Exception as e:
            print(e)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print("EE", e)
            return "127.0.0.1"

    async def scan_network(self, port=8266):
        await asyncio.sleep(0)
        if not self.IS_SCANNING:
            self.IS_SCANNING = True
            try:
                local_ip = self.get_local_ip()
                print(local_ip)
                ip = local_ip.split(".")
                print("Starting Scan...")
                for i in range(255):
                    socket_obj = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    #socket_obj.setblocking(0)
                    socket.setdefaulttimeout(.1)
                    addr = "{}.{}.{}.{}".format(ip[0], ip[1], ip[2], i)
                    print("Scanning Addr: {}".format(addr) )
                    result = socket_obj.connect_ex((addr,port))
                    await asyncio.sleep(0)
                    #socket.setdefaulttimeout(None)
                    print(result)
                    if result == 0:
                        print("found")
                        self.SCAN_IPS.append(addr)
                    socket_obj.close()
                print("SCAN_IPS", self.SCAN_IPS)
                self.IS_SCANNING = False
                return self.SCAN_IPS
            except Exception as e:
                print(e)
                self.IS_SCANNING = False
                return self.SCAN_IPS



network_scanner = NetworkScanner()
