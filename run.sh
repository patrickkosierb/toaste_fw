#!/bin/bash

cleanup(){
    pkill python3
    exit 0
}

trap cleanup SIGINT

sleep 1

python3 main_rev2.py

wait -n

cleanup
