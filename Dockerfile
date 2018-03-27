FROM ubuntu:16.04

RUN apt-get update && apt-get install cron -y
RUN apt-get install python3-pip python3-dev nginx -y

RUN mkdir -p /code/wordknow
WORKDIR /code
ADD ./requirements.txt /code/requirements.txt

RUN pip3 install -r requirements.txt  # --no-cache
ADD ./wordknow ./wordknow

RUN pip3 install --upgrade pip

RUN rm -rf /etc/localtime && ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

RUN apt-get install postgresql postgresql-contrib -y
#RUN psql postgres -c "CREATE USER wordknow WITH PASSWORD '123';"
#RUN psql postgres -c "ALTER ROLE wordknow SET timezone TO 'UTC';"
#RUN psql postgres -c "CREATE DATABASE wordknow_db WITH OWNER wordknow;"

RUN pip3 install gunicorn  # TODO в requirements.txt
