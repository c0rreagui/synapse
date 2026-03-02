-- Migration: Anti-Detect Fingerprint Columns
-- Date: 2026-02-27
-- Description: Adds proxy, browser fingerprint, and geolocation columns to profiles table
-- for per-profile browser identity isolation.

-- Proxy Identity
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proxy_server VARCHAR DEFAULT NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proxy_username VARCHAR DEFAULT NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proxy_password VARCHAR DEFAULT NULL;

-- Browser Fingerprint
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS fingerprint_ua VARCHAR DEFAULT NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS fingerprint_viewport_w INTEGER DEFAULT 1920;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS fingerprint_viewport_h INTEGER DEFAULT 1080;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS fingerprint_locale VARCHAR DEFAULT 'pt-BR';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS fingerprint_timezone VARCHAR DEFAULT 'America/Sao_Paulo';

-- Geolocation (Consistent with Proxy IP)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS geolocation_latitude VARCHAR DEFAULT NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS geolocation_longitude VARCHAR DEFAULT NULL;
