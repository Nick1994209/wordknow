#!/usr/bin/env bash

echo "
BEFORE RUNNING SCRIPT generate pub key and set to github

    $ ssh-keygen
    $ cat ~/.ssh/id_rsa.pub  # and add to github
    $ apt-get update && apt-get install nano -y
"

TELEGRAM_TOKEN=""
while [[ "$1" != "" ]]; do
    case $1 in
        -t | --telegram-token ) shift
                                TELEGRAM_TOKEN=$1
                                ;;
    esac
    shift
done
if [[ "$TELEGRAM_TOKEN" == "" ]]; then
    echo "Script requires one argument - telegram token key from @BotFather
        more additional - https://core.telegram.org/bots#3-how-do-i-create-a-bot

        $ ./install_with_docker_script.sh --telegram-token BOT_API_TOKEN
    "
    exit 1
fi

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

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

SERVER_IP="$(ip route get 1 | awk '{print $7}')"
echo "
TELEGRAM_BOT_KEY="$TELEGRAM_TOKEN"
TELEGRAM_BOT_NAME="@wordknow"
BOT_SITE_URL="http://$SERVER_IP"

# you can add proxy
# http_proxy=host:port
# https_proxy=host:porthttps_proxy=Nono
" >> ./.env
