#!/bin/bash

sudo mkdir /var/run/mydaemon
sudo chown $USER:$USER /var/run/mydaemon
sudo python3 run.py