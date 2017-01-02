# RoHAWKtics Scouting Python Server

[![Build Status](https://travis-ci.org/HVA-FRC-3824/RoHAWKticsScoutingPythonServer.svg?branch=master)](https://travis-ci.org/HVA-FRC-3824/RoHAWKticsScoutingPythonServer)

This is the server to be run at competition for the scouting tablets. It can receive data from the tablets through either bluetooth or adb (usb) and calculates all the metrics for determining the abilities and strategies for teams.


# Running
If using the socket server the adb server must be start with sudo in order to recognise the android devices.
```
  sudo ./adb start-server
  sudo python3 server.py -c config.json
```

# Config
event_key - Event key used by The Blue Alliance. Must also use for the tablets.
socket - whether the socket server should be running
bluetooth - whether the bluetooth server should be running
setup - whether the database should be setup for a new event (must be run the first time for a new event)
log_level - what level of logging is printed to the screen
time_between_cycles - if a cycle finishes faster than this time then the server will wait before starting a new cycle
time_between_caches - time between backing up firebase
report_crash - if on then emails and texts will be sent if a crash happens
aggregate - whether the server should run calculation on the data
