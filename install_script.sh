#!/usr/bin/env bash
echo "https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04"

echo "START"
apt-get update
apt-get install git -y

mkdir /code
cd /code

# ssh-keygen
# cat /root/.ssh/id_rsa.pub  # and add to github

git clone git@github.com:Nick1994209/wordknow.git
apt-get install python3-pip python3-dev cron nginx libpq-dev postgresql postgresql-contrib -y

# sometimes need reinstall locales
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
#dpkg-reconfigure locales

echo "INSTALL REQUIREMENTS"
pip3 install -r requirements.txt

echo "SETUP POSTGRES"
sudo -u postgres psql postgres -c "CREATE USER wordknow WITH PASSWORD '123';"
sudo -u postgres psql postgres -c "ALTER ROLE wordknow SET timezone TO 'UTC';"
sudo -u postgres psql postgres -c "CREATE DATABASE wordknow_db WITH OWNER wordknow;"

cd application


echo "SETUP DJANGO"
#python3 manage.py makemigrations
python3 manage.py migrate
# COLLECT STATIC FOR NGINX
mkdir -p /app_static_files
python3 manage.py collectstatic

# Create an exception for port 8000 by typing; if want run 0.0.0.0:8000
# ufw allow 8000
# for delete ufw delete allow 8000

cd ..

echo "SETUP GUNICORN"

# add /code/wordknow/environments.env

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

 rm /etc/nginx/nginx.conf
 cp etc/nginx.wordknow /etc/nginx/nginx.conf
#cp etc/nginx.wordknow /etc/nginx/sites-available/nginx.wordknow
#ln -s /etc/nginx/sites-available/nginx.wordknow /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
ufw allow 'Nginx Full'
# for nginx logs tail -F /var/log/nginx/error.log


echo "SETUP CRON"
#show cron logs
#grep CRON /var/log/syslog
crontab -e  # set from etc/crontab

# cat /var/spool/cron/crontabs/root
# chown root:root /var/spool/cron/crontabs/root
# chmod 600 /var/spool/cron/crontabs/root
