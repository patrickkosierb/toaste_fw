#!/bin/bash

cleanup(){
    pkill python3
    pkill mosquitto
    exit 0
}

trap cleanup SIGINT

sudo mosquitto -c /etc/mosquitto/mosquitto.conf &

sleep 2

python3 main_rev1v3.py

wait -n

cleanup