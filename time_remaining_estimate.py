import time
import random
import threading

# TODO: find the best values
GUESS_FACTOR_FAR = 600 
GUESS_FACTOR_ALMOST = 70 
GUESS_FACTOR_VERY_CLOSE = 10 

time_estimate_sec = 0

# TODO: make this a class

def rand_error(spread = 10):
    return random.randint(-spread, spread)

def calculate_new_time_estimate(current_crispiness, target_crispiness):
    """Return a time in seconds"""
    print("generating new time estimate")

    if current_crispiness is None or target_crispiness is None:
        return 0

    if current_crispiness >= target_crispiness:
        return 0
    elif current_crispiness == 0:
        return GUESS_FACTOR_FAR*target_crispiness + rand_error()
    
    # vary the error based on how far it is
    error = rand_error(round(target_crispiness/current_crispiness))

    crisp_remaining = target_crispiness - current_crispiness
    new_time_estimate = GUESS_FACTOR_FAR*(crisp_remaining)

    # for closer values we need more accuracy
    # if crisp_remaining < 0.1:
    #     new_time_estimate = GUESS_FACTOR_ALMOST
    
    if crisp_remaining < 0.01:
        new_time_estimate = GUESS_FACTOR_VERY_CLOSE

    global time_estimate_sec
    time_estimate_sec = round(new_time_estimate+error)
    return new_time_estimate

def create_time_tracker(listener_callback):
    global time_estimate_sec
    while(1): # TODO: how to exit?
        time.sleep(1)
        if time_estimate_sec > 0:
            time_estimate_sec = time_estimate_sec - 1
            listener_callback(time_estimate_sec)
            # print("sent new time")


def init(listener_callback):
    time_tracker_thread = threading.Thread(target=create_time_tracker, args=(listener_callback,))
    time_tracker_thread.start()