import ctypes
import enum
from codecs import StreamWriter
from dataclasses import dataclass
from typing import Annotated, TypeVar

class BHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("opcode", ctypes.c_uint16),
        ("size", ctypes.c_uint32)
    ]


HEADER_SIZE = ctypes.sizeof(BHeader)


class BAuth(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("uuid", ctypes.c_char * 36)
    ]


AUTH_SIZE = ctypes.sizeof(BAuth)


class BCallTo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("touuid", ctypes.c_char * 36)
    ]


CALLTO_SIZE = ctypes.sizeof(BCallTo)


class BCallResponse(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("peer_uuid", ctypes.c_char * 36),
        ("peer_ip", ctypes.c_char * 21),
    ]


CALL_RESPONSE_SIZE = ctypes.sizeof(BCallResponse)


class BIncomingCall(ctypes.Structure):
    _pack_ = 1
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
