import threading
import enum
import time
from ble_server.toaste_ble_server import Application, ToastE_Service, ToastE_Advertisement
from ble_server.message_types import MessageTypes

# TODO: queues for data transfer between threads

class State(str, enum.Enum):
    IDLE = 'IDLE'
    CONFIGURED = 'CONFIGURED'
    TOASTING = 'TOASTING'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'


def run_ble(app):
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()
    except Exception as e:
        print(e)

def demo_reader(ble_service):
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
                target = None
                time_remaining_sec = 200
                time_elapsed_sec = 0
                state = State.IDLE
                ble_service.set_cancel_flag(False)
                
            elif (state == State.DONE and target is None):
                crispiness = 0
                time_remaining_sec = 200
                time_elapsed_sec = 0
                state = State.IDLE
            elif (target and crispiness >= target):
                state = State.DONE
            elif (target and target > 0):
                state = State.TOASTING # TODO: this is controlled in main loop
                time_elapsed_sec += 1
                time_remaining_sec -= 2 # TODO: temp for testing
                crispiness += 0.05*time_elapsed_sec # TODO: temp for testing
                crispiness = round(crispiness)
            elif (target): 
                state = State.TOASTING
                x = input("Type to simulate toast done ")
                if x:
                    state = State.DONE
            elif (state == State.IDLE):
                x = input("Type to simulate solenoid lowered ")
                if x:
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


def init(set_crisp_callback=None,cancel_callback=None):
    app = Application()

    ble_service = ToastE_Service(0, set_crisp_callback, cancel_callback)
    app.add_service(ble_service)

    app.register()

    adv = ToastE_Advertisement(0)
    adv.register()

    # start the BLE server
    # run_ble(app)
    ble_thread = threading.Thread(target=run_ble, args=(app,))
    ble_thread.start()

    return ble_service


if __name__ == "__main__":
    print("testing")
    ble_service = init()
    
    # start the BLE reader
    reader_thread = threading.Thread(target=demo_reader, args=(ble_service,))
    reader_thread.start()