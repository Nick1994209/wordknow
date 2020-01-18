FROM python:3.7-alpine3.7

ENV LANG "ru_RU.UTF-8"
ENV LC_COLLATE "C"

RUN apk update && apk add --no-cache \
    build-base \
    jpeg-dev \
    gcc \
    musl-dev \
    postgresql-dev \
    postgresql-libs \
    zlib-dev \
    enchant \
    aspell-en

# now in pyenchant available EN dict

ADD ./requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r ./requirements.txt

RUN mkdir -p /code
COPY . /code
WORKDIR /code/application
