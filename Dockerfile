FROM python:3.7-alpine3.7

RUN apk update && apk add --no-cache \
    build-base \
    jpeg-dev \
    gcc \
    musl-dev \
    postgresql-dev \
    postgresql-libs \
    zlib-dev \
    enchant

ADD ./requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r ./requirements.txt

RUN mkdir -p /code
COPY . /code
WORKDIR /code/application
