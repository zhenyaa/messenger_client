from multiprocessing import get_context

from bus_service import BusService
from udp_client import UDPClient
from tcp_client import TCPClient
from tui import build_app

ctx = get_context()
bus_queue = ctx.Queue()
tcp_queue = ctx.Queue()
udp_queue = ctx.Queue()
tui_queue = ctx.Queue()

routing_table = {
    "tcp.message": [tui_queue],
    "tcp.auth": ["tcp"],
    "udp.packet": [tui_queue],
    "ui.command": [tcp_queue, udp_queue],
    "system.*": ["tui", "tcp", "udp"],
    "tui.warning": ["tui"],
    "tui.*": ["tui"],
}
targets = {
    "tui": tui_queue,
    "tcp": tcp_queue,
    "udp": udp_queue,
}
stop_event = ctx.Event()

if __name__ == "__main__":
    bus_service = BusService(bus_queue, routing_table, targets, stop_event)
    bus_service.start()
    tcp_client = TCPClient(bus_queue, tcp_queue, stop_event)
    tcp_client.start()
    udp_client = UDPClient(bus_queue, udp_queue, stop_event)
    udp_client.start()
    try:
        build_app(bus_queue, tui_queue).run()
    finally:
        stop_event.set()
        tcp_client.join()
        udp_client.join()
        bus_service.join()
