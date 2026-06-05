-- Database initialization script for antifrode_backend
-- This script is optional if using Alembic migrations exclusively

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Optional: Pre-create schema (Alembic will manage the rest)
CREATE SCHEMA IF NOT EXISTS public;
