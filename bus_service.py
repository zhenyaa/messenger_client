from dataclasses import dataclass
from multiprocessing import Process

class BusService(Process):
    def __init__(self, bus_queue, routing_table, targets, stop_event):
        super().__init__()
        self.bus_queue = bus_queue
        self.routing_table = routing_table
        self.targets = targets
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            try:
                event = self.bus_queue.get(timeout=0.5)
                if event is None:
                    continue
                # print("BUS:", event)
                for pattern, targets in self.routing_table.items():
                    if self.match(event.type, pattern):
                        for t in targets:
                            # print("BUS:send to ", t)
                            self.targets[t].put(event)

            except Exception:
                continue

    def match(self, event_type, pattern):
        if pattern.endswith("*"):
            return event_type.startswith(pattern[:-1])
        return event_type == pattern
