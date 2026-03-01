#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check pgvector availability and provide instructions for enabling.

Usage:
    uv run python scripts/enable_pgvector.py
"""

import os
import sys

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(".env.local")

from sqlalchemy import text
from src.fleet_intel_mcp.db.connection import AsyncSessionLocal


async def check_pgvector():
    """Check pgvector availability and provide guidance."""
    
    print("=" * 70)
    print("FleetIntel pgvector Availability Check")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        # Check current user
        result = await session.execute(text("SELECT current_user"))
        user = result.scalar()
        print(f"\nCurrent user: {user}")
        
        # Check if user is superuser
        result = await session.execute(text("SELECT usesuper FROM pg_user WHERE usename = current_user"))
        is_superuser = result.scalar()
        print(f"Is superuser: {is_superuser}")
        
        # Check for pgvector
        result = await session.execute(text(
            "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
        ))
        row = result.fetchone()
        
        if row:
            print(f"\n[OK] pgvector {row.extversion} is installed!")
            return True
        else:
            print("\n[FAIL] pgvector is NOT installed")
            
            # Check all available extensions
            result = await session.execute(text(
                "SELECT extname FROM pg_extension ORDER BY extname"
            ))
            extensions = [r.extname for r in result.fetchall()]
            print(f"\nAvailable extensions ({len(extensions)}):")
            for ext in extensions[:20]:
                print(f"  - {ext}")
            if len(extensions) > 20:
                print(f"  ... and {len(extensions) - 20} more")
            
            print("\n" + "=" * 70)
            print("HOW TO ENABLE pgvector ON SUPABASE")
            print("=" * 70)
            
            print("""
OPTION 1: Enable via Supabase Dashboard (Recommended)
--------------------------------------------------------
1. Go to https://supabase.com/dashboard
2. Select your project: oqupslyezdxegyewwdsz.supabase.co
3. Go to Database > Extensions
4. Search for "vector"
5. Click "Enable" next to pg_vector
6. Wait for the extension to be enabled
7. Run this script again to verify

OPTION 2: Contact Supabase Support (if extension not visible)
--------------------------------------------------------
1. Go to https://supabase.com/dashboard
2. Click the chat bubble (bottom right) or go to Support
3. Request: "Please enable pgvector extension on my project"
4. Project ID: oqupslyezdxegyewwdsz
5. They will enable it within 24 hours (usually faster)

OPTION 3: Upgrade to Pro Plan (includes pgvector)
--------------------------------------------------------
- Free tier may have limited extension support
- Pro plan ($25/mo) guarantees all extensions
- Go to Settings > Billing > Plan to upgrade

AFTER ENABLING:
---------------
Run this script again:
    uv run python scripts/enable_pgvector.py

Then apply migrations:
    uv run python scripts/apply_pgvector_migrations.py
""")
            return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(check_pgvector())
