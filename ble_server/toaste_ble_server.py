#!/usr/bin/python3

import random
import dbus

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from gpiozero import CPUTemperature

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class ToastE_Advertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Toast-E")
        self.include_tx_power = True

class ThermometerService(Service):
    THERMOMETER_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.THERMOMETER_SVC_UUID, True)
        self.add_characteristic(TempCharacteristic(self))
        self.add_characteristic(UnitCharacteristic(self))

    def is_farenheit(self):
        return self.farenheit

    def set_farenheit(self, farenheit):
        self.farenheit = farenheit

class TempCharacteristic(Characteristic):
    TEMP_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.TEMP_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(TempDescriptor(self))

    def get_temperature(self):
        value = []
        unit = "C"

        cpu = CPUTemperature()
        temp = cpu.temperature
        if self.service.is_farenheit():
            temp = (temp * 1.8) + 32
            unit = "F"

        strtemp = str(round(temp, 1)) + " " + unit
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_temperature_callback(self):
        if self.notifying:
            value = self.get_temperature()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_temperature()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_temperature_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_temperature()

        return value

class TempDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "CPU Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TEMP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.UNIT_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(UnitDescriptor(self))

    def WriteValue(self, value, options):
        val = str(value[0]).upper()
        if val == "C":
            self.service.set_farenheit(False)
        elif val == "F":
            self.service.set_farenheit(True)

    def ReadValue(self, options):
        value = []

        if self.service.is_farenheit(): val = "F"
        else: val = "C"
        value.append(dbus.Byte(val.encode()))

        return value

class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Temperature Units (F or C)"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.UNIT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class TimerService(Service):
    # Timer Service
    TIMER_SERVICE_UUID = '0000ffe0-0000-1000-8000-00805f9b34fb'

    def __init__(self, index):
        Service.__init__(self, index, self.TIMER_SERVICE_UUID, True)
        self.add_characteristic(GetTimeCharacteristic(self))

class GetTimeCharacteristic(Characteristic):
    GET_TIME_CHAR_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.GET_TIME_CHAR_UUID,
                ["notify", "read"], service)
        # self.add_descriptor(TempDescriptor(self))

    def get_time_remaining(self):
        value = []
        
        time_sec = random.randint(0, 500)

        strtemp = str(round(time_sec, 1))
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_time_remaining_callback(self):
        if self.notifying:
            value = self.get_time_remaining()
            print("Notification value: " + str(value) + " seconds")
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_time_remaining()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_time_remaining_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_time_remaining()
        print("ReadValue Time Remaining")

        return value

class CrispinessService(Service):
    CRISPINESS_SERVICE_UUID = '0000ffa0-0000-1000-8000-00805f9b34fb'

    def __init__(self, index):
        self.target_crispiness = 0

        Service.__init__(self, index, self.CRISPINESS_SERVICE_UUID, True)
        self.add_characteristic(GetCurrentCrispCharacteristic(self))
        self.add_characteristic(SetTargetCrispCharacteristic(self))

    def set_target_crispiness(self, crispiness):
        self.target_crispiness = crispiness

class GetCurrentCrispCharacteristic(Characteristic):
    CURRENT_CRISP_CHAR_UUID = '0000ffa2-0000-1000-8000-00805f9b34fb'

    def __init__(self, service):
        self.crispiness = 0

        self.notifying = False

        Characteristic.__init__(
                self, self.CURRENT_CRISP_CHAR_UUID,
                ["notify", "read"], service)
        # self.add_descriptor(TempDescriptor(self))

    def get_current_crispiness(self):
        value = []
        
        self.crispiness = self.crispiness + 0.05

        strtemp = str(round(self.crispiness, 2))
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_crispiness_callback(self):

        if self.notifying:
            value = self.get_current_crispiness()
            print("notification value: " + str(value))
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_current_crispiness()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_crispiness_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        print("ReadValue")

        value = self.get_current_crispiness()

        return value
    

class SetTargetCrispCharacteristic(Characteristic):
    TARGET_CRISP_CHAR_UUID = '0000ffa1-0000-1000-8000-00805f9b34fb'

    def __init__(self, service):
        Characteristic.__init__(
                self, self.TARGET_CRISP_CHAR_UUID,
                ["write"], service)
        # self.add_descriptor(TempDescriptor(self))

    def WriteValue(self, value, options):
        print("Received Value: " + str(value))
        val = float(value)

        self.service.set_target_crispiness(val)


# TODO: move to main.py

app = Application()
app.add_service(ThermometerService(0))
app.add_service(TimerService(1))
app.add_service(CrispinessService(2))
app.register()

adv = ToastE_Advertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
