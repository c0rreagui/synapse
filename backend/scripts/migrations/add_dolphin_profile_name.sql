-- Migration: Add dolphin_profile_name to profiles table
-- Stores the display name of the profile inside Dolphin{anty} UI
-- Used by launch_browser_via_dolphin() to click START on the correct profile

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS dolphin_profile_name VARCHAR;
