#!/usr/bin/env bash
sudo ./adb start-server
python3 src/server.py -c config.json
