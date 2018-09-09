FROM python:3.7-alpine3.7

# for psycopg2
RUN apk update && \
 apk add postgresql-libs && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev

ADD ./requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r ./requirements.txt

RUN mkdir -p /code
COPY . /code
WORKDIR /code/application
