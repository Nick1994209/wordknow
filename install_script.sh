#!/usr/bin/env bash

apt-get update
apt-get install python3-pip python3-dev cron nginx libpq-dev postgresql postgresql-contrib -y

pip install -r wordknow/requirements.txt

# SETUP POSTGRES
add_postgres_db_with_user "wordknow_db" "wordknow" "123"

# COLLECT STATIC FOR NGINX
python wordknow/manage.py makemigrations
python wordknow/manage.py migrate
python wordknow/manage.py collectstatic

function add_postgres_db_with_user {
    database=$1;
    user=$2;
    password=$3;
    psql postgres -c "CREATE USER $user WITH PASSWORD '$password';"
    psql postgres -c "ALTER ROLE $user SET timezone TO 'UTC';"
    psql postgres -c "CREATE DATABASE $database WITH OWNER $user;"
}

# Create an exception for port 8000 by typing:
ufw allow 8000

cp etc/gunicorn.service /etc/systemd/system/gunicorn.service
