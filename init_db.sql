CREATE ROLE wordknow WITH LOGIN PASSWORD '123';

CREATE DATABASE wordknow_db WITH
    TEMPLATE = template0
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8';

ALTER DATABASE wordknow_db OWNER TO wordknow;
