-- Runs once, the first time the Postgres container starts with an empty volume.
-- A separate database for tests, so running pytest never wipes your dev data.
CREATE DATABASE urldb_test;
