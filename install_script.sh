#!/usr/bin/env bash

apt-get update && apt-get install cron -y
apt-get install python3-pip python3-dev -y
apt-get install nginx -y

#apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx -y

pip install --no-cache -r requirements.txt

python manage.py collectstatic

