import enum

class MessageTypes(enum.Enum):
    CANCEL = 0x00
    TARGET_CRISPINESS = 0x01
    READ_STATE = 0x02
