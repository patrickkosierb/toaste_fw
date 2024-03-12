#!/bin/bash

cleanup(){
    pkill python3
    pkill mosquitto
    exit 0
}

trap cleanup SIGINT

sudo mosquitto -c /etc/mosquitto/mosquitto.conf &

sleep 2

python3 get_frame3.py &
python3 test2.py #change this to main_loop.py

wait -n

cleanup