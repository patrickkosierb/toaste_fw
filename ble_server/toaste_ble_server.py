#!/usr/bin/python3

import dbus
import json

from ble_server.advertisement import Advertisement
from ble_server.service import Application, Service, Characteristic, Descriptor

from ble_server.message_types import MessageTypes


GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 1000

class ToastE_Advertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Toast-E")
        self.include_tx_power = True
        

class ToastE_Service(Service):
    TOAST_E_SERVICE_UUID = "00000023-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index, set_crisp_callback, cancel_callback):
        # incomming data
        self._target_crispiness = None
        self.cancel_flag = False

        # outgoing data
        self.crispiness = 0
        self.time_remaining = None
        self.time_elapsed = 0 # seconds
        self.state = 'IDLE'

        # callbacks
        self.set_crisp_callback = set_crisp_callback
        self.cancel_callback = cancel_callback

        Service.__init__(self, index, self.TOAST_E_SERVICE_UUID, True)
        self.add_characteristic(ToastE_Characteristic(self))

    def set_target_crispiness(self, crispiness):
        self._target_crispiness = crispiness
        if self.set_crisp_callback:
            self.set_crisp_callback(crispiness)

    # def set_cancel_flag(self, cancel: bool):
    #     self.cancel_flag = cancel
    #     # Temp for now:
    #     self.set_target_crispiness(None)

    #     if self.cancel_callback:
    #         self.cancel_callback()

    def get_current_crispiness(self):
        return self.crispiness
    
    def get_state(self):
        return self.state

    """ Access from outside BLE module """
    def get_target_crispiness(self):
        return self._target_crispiness
    
    def get_cancel_flag(self):
        return self.cancel_flag
    
    def set_current_crispiness(self, crispiness):
        self.crispiness = round(crispiness*100)

    def set_state(self, state):
        self.state = state

    def set_time_remaining(self, time_sec):
        self.time_remaining = time_sec

    def set_time_elapsed(self, time_elapsed_sec):
        self.time_elapsed = time_elapsed_sec


class ToastE_Characteristic(Characteristic):
    TOAST_E_CHAR_UUID = "00000021-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):

        self.notifying = False

        Characteristic.__init__(
                self, self.TOAST_E_CHAR_UUID,
                ["notify", "read", "write"], service)
        self.add_descriptor(ToastE_Descriptor(self))

    def build_state_payload(self):
        crispiness = self.service.get_current_crispiness()
        state = self.service.get_state()
        
        payload = {'controller_state': state, 'current_crispiness': crispiness, 'target_crispiness': self.service.get_target_crispiness(), 'time_remaining_estimate': self.service.time_remaining, 'time_elapsed': self.service.time_elapsed}
        # print('ble payload', payload)
        
        try:
            payload_bytes = json.dumps(payload).encode('utf-8')
        except Exception as e:
            print(e)
            raise e
        
        # encode in byte array
        value = []
        for v in payload_bytes:
            value.append(dbus.Byte(v))

        return value

    def create_notification_callback(self):
        if self.notifying:
            value = self.build_state_payload()
            # print("notification value: " + str(value))
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        print("Start Notify command received for ToastE_Characteristic")
        self.notifying = True

        value = self.build_state_payload()

        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.create_notification_callback)

    def StopNotify(self):
        self.notifying = False
        print("Stop Notify command received for ToastE_Characteristic")

    def ReadValue(self, options):
        value = self.build_state_payload()
        return value
    
    def WriteValue(self, value, options):
        # TODO: extract command from value
        print("WriteValue: " + str(value))
        try:
            command = int(value[0])

            if command == MessageTypes.CANCEL:
                print("Cancel command received")
                if self.cancel_callback:
                    self.service.cancel_callback()
                self.service.set_target_crispiness(None)
                # self.service.set_cancel_flag(True)
            elif command == MessageTypes.TARGET_CRISPINESS:
                print("Received Target Crispiness Value: ")
                data = [int(val) for val in value[1:]]
                print(data)
                self.service.set_target_crispiness(data[0])
                # self.service.set_target_crispiness(int(value[1]))
            elif command == MessageTypes.RESET:
                self.service.set_target_crispiness(None)
            else:
                print("Command not recognised", command)
        except Exception as e:
            print(e)

class ToastE_Descriptor(Descriptor):
    DESCRIPTOR_UUID = "1313"
    DESCRIPTOR_VALUE = "Target Crispiness (range 0.0-1.0)" # TODO: add description

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value