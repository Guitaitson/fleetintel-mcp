#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for agent queries."""

import asyncio
import os
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env.local
load_dotenv(project_root / '.env.local', override=True)

from agent.agent import run_query


async def main():
    print('=' * 50)
    print('Testing FleetIntel Agent')
    print('=' * 50)
    
    queries = [
        'qual empresa mais emplacou em 2025?',
        'quantos veiculos tem no banco?',
        'quantos caminhoes a addiante comprou em 2025?',
    ]
    
    for query in queries:
        print(f'\nQuery: {query}')
        print('-' * 40)
        try:
            result = await run_query(query)
            print(f'Result: {result}')
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        print()


if __name__ == '__main__':
    asyncio.run(main())
