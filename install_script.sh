#!/usr/bin/env bash
echo "https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04"

echo "START"
#apt-get update
#apt-get install git
#git clone git@github.com:Nick1994209/wordknow.git
apt-get install python3-pip python3-dev cron nginx libpq-dev postgresql postgresql-contrib -y



echo "INSTALL REQUIREMENTS"
pip install -r requirements.txt

echo "SETUP POSTGRES"
add_postgres_db_with_user "wordknow_db" "wordknow" "123"

# COLLECT STATIC FOR NGINX
echo "SETUP DJANGO"
python application/manage.py makemigrations
python application/manage.py migrate
python application/manage.py collectstatic

# Create an exception for port 8000 by typing; if want run 0.0.0.0:8000
# ufw allow 8000
# for delete ufw delete allow 8000

echo "SETUP GUNICORN"
cp etc/gunicorn.service /etc/systemd/system/gunicorn.service
systemctl start gunicorn
systemctl enable gunicorn
systemctl status gunicorn

journalctl -u gunicorn
# IF gunicorn err
# setup /etc/systemd/system/gunicorn.service and restart
# systemctl daemon-reload
# systemctl restart gunicorn

echo "SETUP NGINX"
cp etc/nginx.wordknow /etc/nginx/sites-available/nginx.wordknow
ln -s /etc/nginx/sites-available/nginx.wordknow /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
ufw allow 'Nginx Full'
# for nginx logs tail -F /var/log/nginx/error.log

# ------------ utils --------------
function add_postgres_db_with_user {
    database=$1;
    user=$2;
    password=$3;
    psql postgres -c "CREATE USER $user WITH PASSWORD '$password';"
    psql postgres -c "ALTER ROLE $user SET timezone TO 'UTC';"
    psql postgres -c "CREATE DATABASE $database WITH OWNER $user;"
}
