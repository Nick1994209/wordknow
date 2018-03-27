#!/usr/bin/env bash

cd /code/wordknow/application
/usr/bin/python3 manage.py telegram_tasks > /logs/console_telegram_tasks.logs
