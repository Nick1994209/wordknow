#!/usr/bin/env bash

echo ```BEFORE RUNNING SCRIPT generate pub key and set to github

    $ ssh-keygen
    $ cat ~/.ssh/id_rsa.pub  # and add to github
    $ apt-get update && apt-get install nano -y
```

set -o errexit
set -o xtrace
set -o nounset

test -e ~/.ssh/id_rsa.pub

apt-get update
apt-get install git nano docker docker-compose -y

mkdir /code
cd /code

git clone git@github.com:Nick1994209/wordknow.git

cd wordknow
docker-compose run server python manage.py migrate
# if required
#docker-compose run server python manage.py shell -c \
# "from django.contrib.auth.models import User; User.objects.create_superuser('admin', '', 'pass')"

apt-get install nginx -y
echo "SETUP NGINX"

rm /etc/nginx/nginx.conf
cp eetc/nginx.wordknow.docker-compose /etc/nginx/nginx.conf
nginx -t  # check nginx config is ok
systemctl restart nginx
# for nginx logs  $ tail -F /var/log/nginx/error.log

ufw allow 'Nginx Full'
ufw status

nohup docker-compose up &
