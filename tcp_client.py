import socket
from multiprocessing import Process

from event_declar import Event
from masseges import *
import ctypes
from time import sleep


class TCPClient(Process):
    def __init__(self, bus_queue, tcp_queue, stop_event):
        super().__init__()
        self.user_uuid = None
        self.tcp_queue = tcp_queue
        self.bus_queue = bus_queue
        self.stop_event = stop_event
        self.state = 'WAIT_HEADER'
        self.header_buf = bytearray()
        self.body_buf = bytearray()
        self.current_opcode = 0
        self.current_body_size = 0
        self.buffer = bytearray()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5555))
        # auth = BAuth()
        # auth.uuid = str(self.user_uuid).encode().ljust(36, b"\0")
        # h = BHeader()
        # h.opcode = OPCODES.AUTH
        # h.size = AUTH_SIZE
        # sock.sendall(bytes(h) + bytes(auth))
        sock.setblocking(False)
        while not self.stop_event.is_set():
            sleep(0.1)
            try:
                cmd = self.tcp_queue.get_nowait()
                self.handle_command(sock, cmd)
            except Exception:
                pass
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
                print({"type": "call_response", "peer": str(payload.peer_uuid), "ip": str(payload.peer_ip)})
                # self.out_q.put({"type": "call_response", "peer": str(payload.peer_uuid), "ip":str(payload.peer_ip)})
                self.out_q.put({"type": "call_response"})
            case OPCODES.INCOMING_CALL:
                print({"type": "incoming_call", "peer": str(payload.call_from), "ip": str(payload.peer_ip)})
                # self.out_q.put({"type": "incoming_call", "peer": str(payload.call_from), "ip": str(payload.peer_ip)})
                self.out_q.put({"type": "incoming_call"})
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

    def handle_command(self, sock, cmd_dict):
        # print("tcp handle event ",cmd_dict)
        cmd = cmd_dict
        if cmd.type == "tcp.call":
            self.send_call(sock, cmd["target"])
        elif cmd.type == "tcp.auth":
            # print("tcp auth event ",cmd)
            if not self.user_uuid:
                self.bus_queue.put(Event("tui.warning", "tcp", {"msg":"user was connected"}))
            auth = BAuth()
            auth.uuid = str(cmd.payload.get("auth")).encode().ljust(36, b"\0")
            h = BHeader()
            h.opcode = OPCODES.AUTH
            h.size = AUTH_SIZE
            sock.sendall(bytes(h) + bytes(auth))
            self.user_uuid = auth.uuid
            self.bus_queue.put(Event("tui.info", "tcp", {"msg": "user connected"}))

        elif cmd.type == "system.shutdown":
            self.stop_event.set()
