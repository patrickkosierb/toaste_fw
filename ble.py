import threading
import enum
import time
from ble_server.toaste_ble_server import Application, ToastE_Service, ToastE_Advertisement
from ble_server.message_types import MessageTypes


class State(str, enum.Enum):
    IDLE = 'IDLE'
    CONFIGURED = 'CONFIGURED'
    TOASTING = 'TOASTING'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'


def start_ble(app):
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()
    except Exception as e:
        print(e)

def reader(ble_service):
    crispiness = 0
    time_remaining_sec = 200
    time_elapsed_sec = 0
    state = State.IDLE

    target = None
    try:
        while(1):
            time.sleep(1)

            target = ble_service.get_target_crispiness()
        
            # read ble service
            if (ble_service.get_cancel_flag()):
                state = State.CANCELLED

                # TODO: remove this 
                # temp reset
                crispiness = 0
                time_remaining_sec = 200
                time_elapsed_sec = 0
                state = State.IDLE
                ble_service.set_cancel_flag(False)

            elif (target and crispiness >= target):
                state = State.DONE
            elif (target and target > 0):
                state = State.TOASTING
                time_elapsed_sec += 1
                time_remaining_sec -= 1
                crispiness += 0.1*time_elapsed_sec
            elif (target): 
                state = State.CONFIGURED
            else:
                # no change
                continue

            # update ble service
            ble_service.set_current_crispiness(crispiness)
            ble_service.set_state(state)
            ble_service.set_time_remaining(time_remaining_sec)
            ble_service.set_time_elapsed(time_elapsed_sec)

            print('target:', target, '\ncurrent:', crispiness,'\nstate:', state, '\ntime_elap:', time_elapsed_sec, '\n')
    except Exception as e:
        print(e)

if __name__ == "__main__":
    app = Application()

    ble_service = ToastE_Service(0)
    app.add_service(ble_service)

    app.register()

    adv = ToastE_Advertisement(0)
    adv.register()

    # start the BLE server
    # start_ble(app)
    ble_thread = threading.Thread(target=start_ble, args=(app,))
    ble_thread.start()

    # start the BLE reader
    reader_thread = threading.Thread(target=reader, args=(ble_service,))
    reader_thread.start()