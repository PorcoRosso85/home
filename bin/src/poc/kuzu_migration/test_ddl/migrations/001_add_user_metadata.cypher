-- Migration: Add metadata to User table
-- Add bio and location fields to existing User nodes

ALTER TABLE User ADD COLUMN bio STRING;
ALTER TABLE User ADD COLUMN location STRING;
ALTER TABLE User ADD COLUMN updated_at TIMESTAMP DEFAULT now();