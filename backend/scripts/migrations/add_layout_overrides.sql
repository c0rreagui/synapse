-- Migration to add layout_mode_overrides column to clip_jobs table
ALTER TABLE clip_jobs ADD COLUMN layout_mode_overrides JSON;
