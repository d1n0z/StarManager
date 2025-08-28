#!/bin/bash

tmux kill-session -t bot
tmux new -s bot -d
tmux send-keys -t bot 'cd /opt/StarManager/' ENTER '. /opt/StarManager/venv/bin/activate' ENTER 'python3.11 main.py' ENTER
