import enum
import socket
import struct
import uuid
import argparse
from multiprocessing import Process, Queue
import socket
import select
import struct
from multiprocessing import Process, Queue
from queue import Empty

import ctypes

HEADER_FMT = "<HI"

UUID_FIELD_SIZE = 36


class BHeader(ctypes.Structure):
    _fields_ = [
        ("opcode", ctypes.c_uint16),
        ("size", ctypes.c_uint32)
    ]


HEADER_SIZE = ctypes.sizeof(BHeader)


class BAuth(ctypes.Structure):
    _fields_ = [
        ("uuid", ctypes.c_char * 36)
    ]


AUTH_SIZE = ctypes.sizeof(BAuth)


class BCallTo(ctypes.Structure):
    _fields_ = [
        ("touuid", ctypes.c_char * 36)
    ]


CALLTO_SIZE = ctypes.sizeof(BCallTo)


class BCallResponse(ctypes.Structure):
    _fields_ = [
        ("peer_uuid", ctypes.c_char * 36),
        ("peer_ip", ctypes.c_char * 21),
    ]


CALL_RESPONSE_SIZE = ctypes.sizeof(BCallResponse)


class BIncomingCall(ctypes.Structure):
    _fields_ = [
        ("call_from", ctypes.c_char * 36),
        ("peer_ip", ctypes.c_char * 21),
    ]


INCOMING_CALL_SIZE = ctypes.sizeof(BIncomingCall)


class OPCODES(enum.IntEnum):
    AUTH = 1,
    PING = 2,
    CALL = 3,
    INCOMING_CALL = 4,
    CALL_RESPONSE = 5


class NetworkProcess(Process):
    def __init__(self, user_uuid, in_q, out_q):
        super().__init__()
        self.user_uuid = user_uuid
        self.in_q = in_q
        self.out_q = out_q
        self.state = 'WAIT_HEADER'
        self.header_buf = bytearray()
        self.body_buf = bytearray()
        self.current_opcode = 0
        self.current_body_size = 0
        self.buffer = bytearray()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5555))
        auth = BAuth()
        auth.uuid = str(self.user_uuid).encode().ljust(32, b"\0")
        h = BHeader()
        h.opcode = OPCODES.AUTH
        h.size = AUTH_SIZE
        sock.sendall(bytes(h) + bytes(auth))
        sock.setblocking(False)
        while True:
            if not self.in_q.empty():
                cmd = self.in_q.get()
                if cmd["type"] == "exit":
                    break
                elif cmd["type"] == "call":
                    self.send_call(sock, cmd["target"])

            try:
                data = sock.recv(4096)
                if data:
                    self.buffer.extend(data)
                    self.parse()
            except BlockingIOError:
                pass
        sock.close()

    def send_call(self, sock, target):
        call = BCallTo()
        call.touuid = str(target).encode().ljust(32, b"\0")
        h = BHeader()
        h.opcode = 3
        h.size = ctypes.sizeof(BCallTo)
        sock.sendall(bytes(h) + bytes(call))

    def handle_packet(self, opcode, payload):
        print(opcode, payload)
        match opcode:
            case OPCODES.CALL_RESPONSE:
                print({"type": "call_response", "peer": str(payload.peer_uuid), "ip":str(payload.peer_ip)})
                self.out_q.put({"type": "call_response", "peer": str(payload.peer_uuid), "ip":str(payload.peer_ip)})
            case OPCODES.INCOMING_CALL:
                print({"type": "incoming_call", "peer": str(payload.call_from), "ip": str(payload.peer_ip)})
                self.out_q.put({"type": "incoming_call", "peer": str(payload.call_from), "ip": str(payload.peer_ip)})
            case _:
                print("could not find")


    def parse(self):
        row_header = self.buffer[:HEADER_SIZE]
        header = BHeader.from_buffer_copy(row_header)
        packet_size = HEADER_SIZE + header.size
        match header.opcode:
            case OPCODES.CALL:
                print("call")
            case OPCODES.INCOMING_CALL:
                data = BIncomingCall.from_buffer_copy(self.buffer, HEADER_SIZE)
                print(data.peer_ip, "incomming call from")
                self.handle_packet(header.opcode, data)
            case OPCODES.CALL_RESPONSE:
                data = BCallResponse.from_buffer_copy(self.buffer, HEADER_SIZE)
                print(data.peer_ip, "call to")
                self.handle_packet(header.opcode, data)
        del self.buffer[:packet_size]


class MainProcess:
    def __init__(self, in_q, out_q):
        self.in_q = in_q
        self.out_q = out_q

    def run(self):
        print("Client started")
        print("Commands: call <uuid>, exit")
        while True:
            print("awhait")
            while not self.out_q.empty():
                event = self.out_q.get()
                self.handle_event(event)

            cmd = input("> ")
            if cmd.startswith("call "):
                target = cmd.split(" ")[1]
                self.in_q.put({
                    "type": "call",
                    "target": target
                })

            elif cmd == "exit":
                self.in_q.put({"type": "exit"})
                break

    def handle_event(self, event):
        print(event)
        if event["type"] == "call_response":
            print(f"\n📞 call_response {event}")
        elif event["type"] == "incoming_call":
            print("\n✅ Authenticated", event)
        else:
            print("\n[server]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", type=uuid.UUID, required=True)
    args = parser.parse_args()

    in_q = Queue()
    out_q = Queue()

    net = NetworkProcess(args.uuid, in_q, out_q)
    net.start()

    cli = MainProcess(in_q, out_q)
    cli.run()

    net.join()
