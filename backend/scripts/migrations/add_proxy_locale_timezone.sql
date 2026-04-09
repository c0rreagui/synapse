-- Migration: add fingerprint_locale and fingerprint_timezone to proxies table
ALTER TABLE proxies ADD COLUMN IF NOT EXISTS fingerprint_locale VARCHAR;
ALTER TABLE proxies ADD COLUMN IF NOT EXISTS fingerprint_timezone VARCHAR;
