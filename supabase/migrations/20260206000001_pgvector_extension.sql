-- FleetIntel pgvector Extension Migration
-- Enable vector extension for similarity search
-- Generated: 2026-02-06

-- Enable pgvector extension
-- This must be run as a superuser or with CREATE EXTENSION permission
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Expected output:
-- | extname | extversion |
-- |---------|------------|
-- | vector  | 0.7.1      |

-- Note: For Supabase, this may already be enabled by default
-- If you get permission errors, contact Supabase support to enable it
