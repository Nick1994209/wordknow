CREATE DATABASE wordknow_db;

CREATE USER wordknow WITH ENCRYPTED PASSWORD '123';
GRANT ALL PRIVILEGES ON DATABASE wordknow_db TO wordknow;