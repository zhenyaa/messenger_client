import socket
from multiprocessing import Process

from event_declar import Event
from masseges import *
import ctypes


class UDPClient(Process):
    def __init__(self, bus_queue, udp_queue, stop_event):
        super().__init__()
        self.user_uuid = None
        self.udp_queue = udp_queue
        self.stop_event = stop_event
        self.bus_queue = bus_queue

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        header = BHeader()
        header.opcode = 1
        header.size = ctypes.sizeof(BAuth)
        auth = BAuth()
        auth.uuid = str(self.user_uuid).encode().ljust(36, b"\0")
        packet = bytes(header) + bytes(auth)
        sock.sendto(packet, ("127.0.0.1", 1111))
        self.bus_queue.put(Event("tui.info", "udp", {"msg": "UDPs connected"}))
        while not self.stop_event.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                self.bus_queue.put(Event("tui.recuv", "udp", {"msg": data.decode()}))

            except socket.timeout:
                pass
            try:
                cmd = self.udp_queue.get_nowait()
                print("UDP CMD:", cmd)

            except Exception:
                pass
