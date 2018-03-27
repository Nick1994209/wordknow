#!/usr/bin/env bash

cd /code/wordknow/application
/usr/bin/python3 manage.py telegram > /logs/console_telegram.logs
