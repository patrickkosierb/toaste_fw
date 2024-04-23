import time
import random

# TODO: find the best values
GUESS_FACTOR_FAR = 600 
GUESS_FACTOR_ALMOST = 70 
GUESS_FACTOR_VERY_CLOSE = 15 

def rand_error(spread = 10):
    return random.randint(-spread, spread)

def get_new_time_remaining(current_crispiness, target_crispiness):
    """Return a time in seconds"""

    if current_crispiness is None or target_crispiness is None:
        return 0

    if current_crispiness >= target_crispiness:
        return 0
    elif current_crispiness == 0:
        return GUESS_FACTOR_FAR*target_crispiness + rand_error()
    
    # vary the error based on how far it is
    error = rand_error(round(target_crispiness/current_crispiness))

    crisp_remaining = target_crispiness - current_crispiness
    time_estimate = GUESS_FACTOR_FAR*(crisp_remaining)

    # for closer values we need more accuracy
    if crisp_remaining < 0.1:
        return GUESS_FACTOR_ALMOST + error 
    
    elif crisp_remaining < 0.02:
        return GUESS_FACTOR_VERY_CLOSE + error

    return round(time_estimate + error)