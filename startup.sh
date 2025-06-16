#!/bin/bash

pkill python

tmux new -s bot -d
tmux send-keys -t bot 'cd /root/StarManager/' ENTER '. /root/StarManager/venv/bin/activate' ENTER 'python3.11 main.py' ENTER

tmux new -s site -d
tmux send-keys -t site 'cd /root/StarManager/site' ENTER '. /root/StarManager/venv/bin/activate' ENTER 'fastapi run main.py --host 127.0.0.1 --port 5000' ENTER
