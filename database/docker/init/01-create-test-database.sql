-- Runs once when the postgres container initializes its data directory.
-- Creates the dedicated test database so the backend test suite works
-- out of the box (docker compose up -d postgres).
CREATE DATABASE cloudvault_test;
