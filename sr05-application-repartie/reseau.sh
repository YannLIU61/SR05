#!/bin/bash

# Create named pipes, one input and one output per process.
mkfifo /tmp/in1 /tmp/out1
mkfifo /tmp/in2 /tmp/out2
mkfifo /tmp/in3 /tmp/out3
mkfifo /tmp/in4 /tmp/out4
mkfifo /tmp/in5 /tmp/out5

# Starting the processes
python3 node.py --auto --ident=node-1 < /tmp/in1 > /tmp/out1 &
python3 node.py --auto --ident=node-2 < /tmp/in2 > /tmp/out2 &
python3 node.py --auto --ident=node-3 < /tmp/in3 > /tmp/out3 &
python3 node.py --auto --ident=node-4 < /tmp/in4 > /tmp/out4 &
python3 node.py --auto --ident=node-5 < /tmp/in5 > /tmp/out5 &

# Waiting for the link creation (security delay)
sleep 1

# Links creation: output -> input
cat /tmp/out1 | tee /tmp/in3 /tmp/in4 &
cat /tmp/out2 | tee /tmp/in4 /tmp/in5 &
cat /tmp/out3 | tee /tmp/in1 /tmp/in5 &
cat /tmp/out4 | tee /tmp/in1 /tmp/in2 &
cat /tmp/out5 | tee /tmp/in1 /tmp/in3 &
