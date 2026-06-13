import ctypes
from codecs import StreamWriter
from dataclasses import dataclass
from typing import Annotated, TypeVar

class BHeader(ctypes.Structure):
    _fields_ = [
        ("opcode", ctypes.c_uint16),
        ("size", ctypes.c_uint32)
    ]

class BPing(ctypes.Structure):
    _fields_ = [
        ("message", ctypes.c_char * 8)
    ]

class BAuth(ctypes.Structure):
    _fields_ = [
        ("uuid", ctypes.c_char * 36)
    ]


