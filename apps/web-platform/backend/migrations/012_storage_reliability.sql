-- Storage reliability metadata for original binaries.
ALTER TABLE books ADD COLUMN IF NOT EXISTS binary_sha256 TEXT;
ALTER TABLE media_assets ADD COLUMN IF NOT EXISTS binary_storage TEXT;
ALTER TABLE media_assets ADD COLUMN IF NOT EXISTS binary_path TEXT;
ALTER TABLE media_assets ADD COLUMN IF NOT EXISTS binary_sha256 TEXT;
