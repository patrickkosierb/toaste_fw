from enum import IntFlag

class MessageTypes(IntFlag):
    TARGET_CRISPINESS = 0x01
    READ_STATE = 0x02
    CANCEL = 0x03
    RESET = 0x04
