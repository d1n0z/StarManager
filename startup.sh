#!/bin/bash

pkill python

tmux new -s bot -d
tmux send-keys -t bot 'cd /root/StarManager/' ENTER '. /root/StarManager/venv/bin/activate' ENTER 'python3.11 main.py' ENTER
