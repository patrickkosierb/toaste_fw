import threading
import time
from ble_server.toaste_ble_server import Application, ThermometerService, StateService, TimerService, CrispinessService, ToastE_Advertisement, State

# TODO: notification service? 
notification_payload = {'state': State.CONFIGURED, 'current_crispiness': 0.0, 'target_crispiness': 0.0, 'time_remaining': 0.0}


def start_ble(app):
    try:
        app.run()
        
    except KeyboardInterrupt:
        app.quit()

def reader(app):
    time.sleep(10)
    # access the services and characteristics
    print(app.GetManagedObjects())


def main():
    app = Application()
    app.add_service(ThermometerService(3))
    app.add_service(StateService(2))
    app.add_service(TimerService(1))
    app.add_service(CrispinessService(0))
    app.register()

    adv = ToastE_Advertisement(0)
    adv.register()

    # start the BLE server
    ble_thread = threading.Thread(target=start_ble, args=(app,))
    ble_thread.start()

    # start the BLE reader
    reader_thread = threading.Thread(target=reader, args=(app,))
    reader_thread.start()