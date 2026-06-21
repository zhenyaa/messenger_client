import asyncio
from collections import deque
from queue import Queue, Empty

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, CompletionsMenu
from prompt_toolkit.layout.containers import HSplit, Window, Float, FloatContainer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

from event_declar import Event

LOG_SIZE = 5
log_state = deque(maxlen=LOG_SIZE)

event_queue = Queue()

def render_log():
    return "\n".join(log_state)

async def worker():
    i = 0
    while True:
        i += 1
        event_queue.put(f"[worker] tick {i}")
        await asyncio.sleep(1.5)

user_compliter = WordCompleter( [
    "exit",
    "call",
    "connect"
])

def build_app(bus_queue, tui_queue):
    global event_queue
    event_queue = tui_queue

    input_buffer = Buffer(completer=user_compliter, complete_while_typing=True)

    log_view = Window(
        content=FormattedTextControl(text=render_log),
        wrap_lines=False,
        height=8,
    )

    input_view = Window(
        BufferControl(buffer=input_buffer),
        height=1,
    )

    body = FloatContainer(
        content=HSplit([
            log_view,
            Window(height=1, char="-"),
            input_view,
        ]),
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(),
            )
        ],
    )

    kb = KeyBindings()

    app = Application(
        layout=Layout(body),
        key_bindings=kb,
        full_screen=False,
    )

    def on_enter(event):
        text = input_buffer.text
        input_buffer.text = ""

        if text:
            log_state.append(f"> {text}")

        if text == "exit":
            bus_queue.put(Event("system.shutdown", "tui", {}))
            event.app.exit()
        if "connect" in text:
            bus_queue.put(Event("tcp.auth", "tui", {"auth": text.split(" ")[1]}))

    @kb.add("enter")
    def _(event):
        on_enter(event)

    @kb.add("c-c")
    def _(event):
        event.app.exit()

    async def event_loop():
        while True:
            try:
                while True:
                    msg:Event = event_queue.get_nowait()

                    log_state.append(f"{msg.type} | {msg.payload}")

            except Empty:
                pass
            app.invalidate()
            await asyncio.sleep(0.05)

    def start():
        # app.create_background_task(worker())
        app.create_background_task(event_loop())
    app.pre_run_callables.append(start)
    return app

if __name__ == "__main__":
    build_app().run()