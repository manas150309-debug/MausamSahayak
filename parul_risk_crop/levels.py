"""Risk levels shared by the whole system.

Ordering matters: UNKNOWN sits ABOVE GREEN on purpose. A station that is silent
or has a faulty sensor must never be reported as "all clear".
"""
from enum import IntEnum


class Level(IntEnum):
    GREEN = 0
    UNKNOWN = 1
    YELLOW = 2
    ORANGE = 3
    RED = 4

    @classmethod
    def from_value(cls, v):
        return cls(int(v))
