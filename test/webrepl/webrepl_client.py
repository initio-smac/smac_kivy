#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import struct
import time
from threading import Thread

try:
    import usocket as socket
except ImportError:
    import socket
import webrepl.websocket_helper as websocket_helper
import zipfile

# Define to 1 to use builtin "uwebsocket" module of MicroPython
USE_BUILTIN_UWEBSOCKET = 0
# Treat this remote directory as a root for file transfers
SANDBOX = ""
#SANDBOX = "/tmp/webrepl/"
DEBUG = 0

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER  = 3
ws = None
sock = None

def debugmsg(msg):
    if DEBUG:
        print(msg)


if USE_BUILTIN_UWEBSOCKET:
    from uwebsocket import websock
else:
    class websock:

        def __init__(self, s):
            self.s = s
            self.buf = b""

        def write(self, data, cmd=False):
            flag = 0x81 if cmd else 0x82
            l = len(data)
            if l < 126:
                # TODO: hardcoded "binary" type
                hdr = struct.pack(">BB", flag, l)
            else:
                hdr = struct.pack(">BBH", flag, 126, l)
            self.s.send(hdr)
            self.s.send(data)

        def recvexactly(self, sz):
            res = b""
            while sz:
                data = self.s.recv(sz)
                if not data:
                    break
                res += data
                sz -= len(data)
            return res

        def read(self, size, text_ok=False):
            if not self.buf:
                while True:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    fl, sz = struct.unpack(">BB", hdr)
                    if sz == 126:
                        hdr = self.recvexactly(2)
                        assert len(hdr) == 2
                        (sz,) = struct.unpack(">H", hdr)
                    if fl == 0x82:
                        break
                    if text_ok and fl == 0x81:
                        break
                    debugmsg("Got unexpected websocket record of type %x, skipping it" % fl)
                    while sz:
                        skip = self.s.recv(sz)
                        debugmsg("Skip data: %s" % skip)
                        sz -= len(skip)
                data = self.recvexactly(sz)
                assert len(data) == sz
                self.buf = data

            d = self.buf[:size]
            self.buf = self.buf[size:]
            assert len(d) == size, len(d)
            return d

        def ioctl(self, req, val):
            assert req == 9 and val == 2


class WebREPLClient:
    ws = None
    sock = None
    CONNECTED = False

    def login(self, ws, passwd):
        while True:
            c = ws.read(1, text_ok=True)
            print("c", c)
            if c == b":":
                assert ws.read(1, text_ok=True) == b" "
                break
        ws.write(passwd.encode("utf-8") + b"\r")

    def read_resp(self, ws):
        data = ws.read(4)
        sig, code = struct.unpack("<2sH", data)
        assert sig == b"WB"
        return code


    def send_req(self, ws, op, sz=0, fname=b""):
        rec = struct.pack(WEBREPL_REQ_S, b"WA", op, 0, 0, sz, len(fname), fname)
        debugmsg("%r %d" % (rec, len(rec)))
        ws.write(rec)


    def get_ver(self, ws):
        self.send_req(ws, WEBREPL_GET_VER)
        # d = ws.read(3)
        d = ws.read(1)
        print("@@ ", d)
        print(len(d))
        # struct.unpack("<BBB", d)
        d = struct.unpack("<B", d)
        return d

    def send_cmd(self, ws, cmd):
        try:
            ws.write(cmd.encode("utf-8") + b"\r\n", cmd=True)
            print("sending cmd", cmd)
            return True
        except Exception as e:
            print("Exception send cmd", e)
            return False


    def put_file(self, ws, local_file, remote_file):
        print("local_file",local_file)
        sz = os.stat(local_file)[6]
        dest_fname = (SANDBOX + remote_file).encode("utf-8")
        rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname)
        debugmsg("%r %d" % (rec, len(rec)))
        ws.write(rec[:10])
        ws.write(rec[10:])
        assert self.read_resp(ws) == 0
        cnt = 0
        with open(local_file, "rb") as f:
            while True:
                sys.stdout.write("Sent %d of %d bytes\r" % (cnt, sz))
                sys.stdout.flush()
                buf = f.read(1024)
                if not buf:
                    break
                ws.write(buf)
                cnt += len(buf)
        assert self.read_resp(ws) == 0

    def get_file(self, local_file, remote_file):
        if self.ws != None:
            content = b""
            src_fname = (SANDBOX + remote_file).encode("utf-8")
            rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_GET_FILE, 0, 0, 0, len(src_fname), src_fname)
            debugmsg("%r %d" % (rec, len(rec)))
            self.ws.write(rec)
            assert self.read_resp(self.ws) == 0
            #with open(local_file, "wb") as f:
            cnt = 0
            while True:
                self.ws.write(b"\0")
                try:
                    ff = self.ws.read(2)
                    print("LEN(ff)", len(ff), ff)
                    (sz,) = struct.unpack("<H", ff)
                    print(sz)
                    if sz == 0:
                        break
                    while sz:
                        buf = self.ws.read(sz)
                        #print(buf)
                        if not buf:
                            raise OSError()
                        cnt += len(buf)
                        content += buf
                        #print(content)
                        #f.write(buf)
                        sz -= len(buf)/2
                        sys.stdout.write("Received %d bytes\r" % cnt)
                        sys.stdout.flush()
                except Exception as e:
                    pass
            content = content[2:]
            #print("CONTENT ", content)
            print(self.read_resp(self.ws))
            assert self.read_resp(self.ws) == 0
            return content.decode(encoding="utf-8")


    def help(self, rc=0):
        exename = sys.argv[0].rsplit("/", 1)[-1]
        print("%s - Perform remote file operations using MicroPython WebREPL protocol" % exename)
        print("Arguments:")
        print("  [-p password] <host>:<remote_file> <local_file> - Copy remote file to local file")
        print("  [-p password] <local_file> <host>:<remote_file> - Copy local file to remote file")
        print("Examples:")
        print("  %s script.py 192.168.4.1:/another_name.py" % exename)
        print("  %s script.py 192.168.4.1:/app/" % exename)
        print("  %s -p password 192.168.4.1:/app/script.py ." % exename)
        sys.exit(rc)

    def error(self, msg):
        print(msg)
        #sys.exit(1)
        self.CONNECTED = False
        if self.sock != None:
            self.sock.close()

    def parse_remote(self, remote):
        host, fname = remote.rsplit(":", 1)
        if fname == "":
            fname = "/"
        port = 8266
        if ":" in host:
            host, port = host.split(":")
            port = int(port)
        return (host, port, fname)

    def connect_ws(self, host, port=8266, passwd=""):
        try:
            s = socket.socket()
            self.sock = s
            ai = socket.getaddrinfo(host, port)
            addr = ai[0][4]
            s.settimeout(3)
            s.connect(addr)
            s.settimeout(None)
            #s = s.makefile("rwb")
            websocket_helper.client_handshake(s)
            self.ws = websock(s)
            #th = Thread(target=self.login, args=(self.ws, str(passwd)))
            #th.daemon = True
            #th.start()
            self.login(self.ws, str(passwd) )
            #print("Remote WebREPL version:", self.get_ver(self.ws))
            print("Remote WebREPL version:", self.ws)
            self.ws.ioctl(9, 2)
            self.CONNECTED = True
            return True
        except Exception as e:
            print("connect err: {}".format(e) )
            self.CONNECTED = False
            return False

    def update_config_variable(self, key, value):
        try:
            if(key == "wifi_config_1") or (key == "wifi_config_2"):
                cmd = "from config import config;config.update_config_variable('{}',{})".format(key, value)
            else:
                cmd = "from config import config;config.update_config_variable('{}','{}')".format(key, value)
            return self.send_cmd(self.ws, cmd)
        except Exception as e:
            print("Except update config variable")

    def send_files(self, zip_file):
        if self.ws != None:
            #try:
                with zipfile.ZipFile(zip_file,"r") as z:
                    zip_files_path = "test_manny"
                    z.extractall(zip_files_path)
                    for filename in z.namelist():
                        print(filename)
                        print(os.path.isdir(filename))
                        #try:
                        #if filename.endswith("/"):
                        if os.path.isdir( zip_files_path + "/" + filename ):
                            f = filename.replace("/", "")
                            self.send_cmd(self.ws, "import os;os.mkdir('{}');".format(f) )
                            time.sleep(.2)
                        else:
                            #time.sleep(.5)
                            print("sending {}".format(filename))
                            self.put_file(self.ws, zip_files_path + "/" + filename, filename)
                            print("{} file sent.\n".format(filename))
                            time.sleep(.2)
                            #s.close()
                    import shutil
                    shutil.rmtree(zip_files_path)
                    return  True
            #except Exception as e:
                print("Exception send files", e)
                return False
        else:
            print("send_files ws not initialised")
            return False

webrepl_client = WebREPLClient()

'''
def main():
    if len(sys.argv) not in (3, 5):
        help(1)

    passwd = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-p':
            sys.argv.pop(i)
            passwd = sys.argv.pop(i)
            break

    if not passwd:
        import getpass
        passwd = getpass.getpass()

    if ":" in sys.argv[1] and ":" in sys.argv[2]:
        error("Operations on 2 remote files are not supported")
    if ":" not in sys.argv[1] and ":" not in sys.argv[2]:
        error("One remote file is required")

    if ":" in sys.argv[1]:
        op = "get"
        host, port, src_file = parse_remote(sys.argv[1])
        dst_file = sys.argv[2]
        if os.path.isdir(dst_file):
            basename = src_file.rsplit("/", 1)[-1]
            dst_file += "/" + basename
    else:
        op = "put"
        host, port, dst_file = parse_remote(sys.argv[2])
        src_file = sys.argv[1]
        if dst_file[-1] == "/":
            basename = src_file.rsplit("/", 1)[-1]
            dst_file += basename

    if True:
        print("op:%s, host:%s, port:%d, passwd:%s." % (op, host, port, passwd))
        print(src_file, "->", dst_file)

    s = socket.socket()

    ai = socket.getaddrinfo(host, port)
    addr = ai[0][4]

    s.connect(addr)
    #s = s.makefile("rwb")
    websocket_helper.client_handshake(s)

    ws = websocket(s)

    login(ws, passwd)
    #print("Remote WebREPL version:", get_ver(ws))

    # Set websocket to send data marked as "binary"
    ws.ioctl(9, 2)

    if op == "get":
        get_file(ws, dst_file, src_file)
    elif op == "put":
        put_file(ws, src_file, dst_file)

    s.close()

'''